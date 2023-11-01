import json
import logging
from datetime import datetime

import inquirer
from django.core.exceptions import ValidationError
from django.db.models import Q
from service.utils.choices import GENDER_ALL
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.participants import find_club
from apps.actions.serializers import RaceSerializer
from apps.entities.services import LeagueService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from pyutils.strings import remove_parenthesis
from rscraping.data.functions import is_memorial, is_play_off
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


def save_race_from_scraped_data(race: RSRace, datasource: Datasource, allow_merges: bool = False) -> Race:
    race.participants = []

    if not race.url:
        raise StopProcessing(f"no datasource provided for {race.race_id}::{race.name}")

    logger.info("preloading trophy & flag")
    (trophy, trophy_edition), (flag, flag_edition) = _retrieve_trophy_and_flag(race)

    logger.info("preloading organizer")
    organizer = find_club(race.organizer) if race.organizer else None

    logger.info("preloading league")
    league = (
        LeagueService.get_by_name(race.league)
        if race.league and not is_play_off(remove_parenthesis(race.name))
        else None
    )

    new_race = Race(
        laps=race.race_laps,
        lanes=race.race_lanes,
        town=race.town,
        type=race.type,
        date=datetime.strptime(race.date, "%d/%m/%Y").date(),
        day=race.day,
        cancelled=race.cancelled,
        cancellation_reasons=[],
        race_name=race.name,
        trophy=trophy,
        trophy_edition=trophy_edition,
        flag=flag,
        flag_edition=flag_edition,
        league=league,
        modality=race.modality,
        gender=race.gender,
        organizer=organizer,
        sponsor=race.sponsor,
        metadata={
            "datasource": [
                MetadataBuilder()
                .ref_id(race.race_id)
                .datasource_name(datasource)
                .values("details_page", race.url)
                .gender(race.gender)
                .build()
            ]
        },
    )

    print(json.dumps(RaceSerializer(new_race).data, indent=4, skipkeys=True, ensure_ascii=False))

    if allow_merges:
        db_race = RaceService.get_by_race(new_race)
        if db_race:
            logger.info(f"{db_race.pk} race found in database matching {race.name}")
            return _merge_race_from_scraped_data(new_race, db_race, ref_id=race.race_id, datasource=datasource)

    logger.info("preloading associated race")
    associated = RaceService.find_associated(
        race=new_race,
        year=datetime.strptime(race.date, "%d/%m/%Y").date().year,
        day=2 if race.day == 1 else 2,
    )

    try:
        return _save_race_from_scraped_data(race=new_race, associated=associated)
    except ValidationError as e:
        if race.day == 1 and inquirer.confirm("Race already in DB. Is this race a second day?"):
            race.day = 2
            return save_race_from_scraped_data(race, datasource=datasource)
        raise e


def _save_race_from_scraped_data(race: Race, associated: Race | None) -> Race:
    if not inquirer.confirm(f"Save new race for {race.name} to the database?", default=False):
        raise StopProcessing(f"Race {race.name} will not be saved")

    race.save()
    if associated and inquirer.confirm(f"Link new race {race.name} with associated {associated.name}"):
        Race.objects.filter(pk=race.pk).update(associated=associated)
        Race.objects.filter(pk=associated.pk).update(associated=race)
        logger.info(f"update {race.pk} associated race with {associated.pk}")
    return race


def _merge_race_from_scraped_data(race: Race, db_race: Race, ref_id: str, datasource: Datasource) -> Race:
    def is_current_datasource(d) -> bool:
        return ("ref_id" in d and d["ref_id"] == ref_id) and d["datasource_name"] == datasource.value

    print(json.dumps(RaceSerializer(db_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    if not inquirer.confirm(f"Found matching race in the database for race {race.name}. Merge both races?"):
        raise StopProcessing

    if not any(is_current_datasource(d) for d in db_race.metadata["datasource"]):
        db_race.metadata["datasource"].append(race.metadata["datasource"][0])
    if db_race.gender != race.gender:
        db_race.gender = GENDER_ALL

    print(json.dumps(RaceSerializer(db_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    if not inquirer.confirm(f"Save new race for {race.name}?", default=False):
        raise StopProcessing

    db_race.save()
    logger.info(f"{db_race.pk} updated with new data")
    return db_race


def _retrieve_trophy_and_flag(race: RSRace) -> tuple[tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
    trophy, flag = None, None
    trophy_edition, flag_edition = None, None
    for name, edition in race.normalized_names:
        if len(race.normalized_names) > 1 and is_memorial(name):
            continue

        if not trophy:
            trophy, trophy_edition = TrophyService.get_closest_by_name_or_none(name), edition
        if not flag:
            flag, flag_edition = FlagService.get_closest_by_name_or_none(name), edition

    if trophy and not trophy_edition:
        edition = _infer_edition(race, trophy=trophy)
        if not edition:
            edition = inquirer.text(f"race_id={race.race_id}::Edition for trophy {race.league}:{trophy}", default=None)
        if edition:
            trophy_edition = int(edition)
        else:
            trophy = None
    if flag and not flag_edition:
        edition = _infer_edition(race, flag=flag)
        if not edition:
            edition = inquirer.text(f"race_id={race.race_id}::Edition for flag {race.league}:{flag}", default=None)
        if edition:
            flag_edition = int(edition)
        else:
            flag = None

    if not trophy and not flag:
        (trophy, trophy_edition), (flag, flag_edition) = _try_manual_input(race.name)

    if not trophy and not flag:
        raise StopProcessing(f"no trophy/flag found for {race.race_id}::{race.normalized_names}")

    return (trophy, trophy_edition), (flag, flag_edition)


def _infer_edition(race: RSRace, trophy: Trophy | None = None, flag: Flag | None = None) -> int | None:
    """
    Infer the edition of a race based on its date, associated trophy, or flag.

    Args:
        race (RSRace): The race for which the edition is to be inferred.
        trophy (Optional[Trophy]): The trophy associated with the race (optional).
        flag (Optional[Flag]): The flag associated with the race (optional).

    Returns:
        Optional[int]: The inferred edition of the race, or None if it cannot be inferred.

    Raises:
        StopProcessing: If neither a trophy nor a flag is provided, the inference cannot be performed.

    The method attempts to infer the edition of a race based on its date, associated trophy, and/or flag. If a trophy
    or flag is provided, it looks for a matching race from the database with the same year and associated trophy or
    flag. If a match is found, the edition of the matching race is returned. If no match is found, it looks for a
    matching race from the previous year, and if found, increments the edition. If no match is found for both the
    current year and the previous year, the edition cannot be inferred, and None is returned.
    """
    if not trophy and not flag:
        raise StopProcessing

    args = {"trophy": trophy} if trophy else {"flag": flag}
    try:
        match = Race.objects.get(
            Q(league__isnull=True) | Q(league__gender=race.gender),
            **args,
            date__year=datetime.strptime(race.date, "%d/%m/%Y").date().year,
            day=1,
        )
        return match.trophy_edition if trophy else match.flag_edition
    except Race.DoesNotExist:
        try:
            args = {"trophy": trophy} if trophy else {"flag": flag}
            match = Race.objects.get(
                Q(league__isnull=True) | Q(league__gender=race.gender),
                **args,
                date__year=datetime.strptime(race.date, "%d/%m/%Y").date().year - 1,
                day=1,
            )
            edition = (match.trophy_edition if trophy else match.flag_edition) or 0
            return edition + 1 if edition else None
        except Race.DoesNotExist:
            return None


def _try_manual_input(name: str) -> tuple[tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
    trophy = flag = None
    trophy_edition = flag_edition = None

    trophy_id = inquirer.text(f"no trophy found for {name}. Trophy ID: ", default=None)
    if trophy_id:
        trophy = Trophy.objects.get(id=trophy_id)
        trophy_edition = int(inquirer.text(f"Edition for trophy {trophy}: ", default=None))

    flag_id = inquirer.text(f"no flag found for {name}. Flag ID: ", default=None)
    if flag_id:
        flag = Flag.objects.get(id=flag_id)
        flag_edition = int(inquirer.text(f"Edition for flag {flag}: ", default=None))

    return (trophy, trophy_edition), (flag, flag_edition)
