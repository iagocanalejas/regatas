import json
import logging
from datetime import datetime

import inquirer
from django.core.exceptions import ValidationError
from utils.choices import GENDER_ALL
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.participants import find_club
from apps.actions.serializers import RaceSerializer
from apps.entities.models import League
from apps.entities.services import LeagueService
from apps.races.models import Flag, FlagEdition, Race, Trophy, TrophyEdition
from apps.races.services import CompetitionService, FlagService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from pyutils.strings import remove_parenthesis
from rscraping.data.functions import is_play_off
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


def save_race_from_scraped_data(race: RSRace, datasource: Datasource, allow_merges: bool = False) -> Race:
    db_race = None
    race.participants = []

    if not race.url:
        raise ValueError(f"no datasource provided for {race.race_id}::{race.name}")

    logger.info("preloading trophy & flag")
    (trophy, trophy_edition), (flag, flag_edition) = _retrieve_trophy_and_flag(race)

    if allow_merges:
        logger.info("preloading race")
        db_race = _retrieve_race(race, trophy, flag)
    if db_race and not trophy:
        trophy, trophy_edition = db_race.trophy, db_race.trophy_edition
    if db_race and not flag:
        flag, flag_edition = db_race.flag, db_race.flag_edition

    if not trophy and not flag:
        raise StopProcessing(f"no trophy/flag found for {race.race_id}::{race.normalized_names}")

    logger.info("preloading organizer")
    organizer = find_club(race.organizer) if race.organizer else None

    logger.info("preloading league")
    league = _retrieve_league(race, db_race)

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
        db_race = RaceService.get_by_race(new_race) if not db_race else db_race
        if db_race:
            logger.info(f"{db_race.pk} race found in database matching {race.name}")
            return _merge_race_from_scraped_data(new_race, db_race, ref_id=race.race_id, datasource=datasource)

    logger.info("preloading associated race")
    associated = RaceService.get_analogous_or_none(
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


def input_race(name: str) -> Race | None:
    race = None
    race_id = inquirer.text(f"no race found for {name}. Race ID", default=None)
    if race_id:
        race = Race.objects.get(id=race_id)
    return race


def input_trophy(name: str) -> TrophyEdition:
    trophy = trophy_edition = None
    trophy_id = inquirer.text(f"no trophy found for {name}. Trophy ID", default=None)
    if trophy_id:
        trophy = Trophy.objects.get(id=trophy_id)
        trophy_edition = int(inquirer.text(f"edition for trophy {trophy}", default=None))
    return trophy, trophy_edition


def input_flag(name: str) -> FlagEdition:
    flag = flag_edition = None
    flag_id = inquirer.text(f"no flag found for {name}. Flag ID", default=None)
    if flag_id:
        flag = Flag.objects.get(id=flag_id)
        flag_edition = int(inquirer.text(f"edition for flag {flag}", default=None))
    return flag, flag_edition


def _merge_race_from_scraped_data(race: Race, db_race: Race, ref_id: str, datasource: Datasource) -> Race:
    def is_current_datasource(d) -> bool:
        return ("ref_id" in d and d["ref_id"] == ref_id) and d["datasource_name"] == datasource.value

    print(json.dumps(RaceSerializer(db_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    if not inquirer.confirm(f"Found matching race in the database for race {race.name}. Merge both races?"):
        raise StopProcessing(f"race {race.name} will not be merged")

    if not any(is_current_datasource(d) for d in db_race.metadata["datasource"]):
        db_race.metadata["datasource"].append(race.metadata["datasource"][0])
    if db_race.gender != race.gender:
        db_race.gender = GENDER_ALL

    print(json.dumps(RaceSerializer(db_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    return _save_race_from_scraped_data(db_race, associated=None)


def _save_race_from_scraped_data(race: Race, associated: Race | None) -> Race:
    if not inquirer.confirm(f"Save new race for {race.name} to the database?", default=False):
        raise StopProcessing(f"race {race.name} will not be saved")

    race.save()
    if associated and inquirer.confirm(f"Link new race {race.name} with associated {associated.name}"):
        Race.objects.filter(pk=race.pk).update(associated=associated)
        Race.objects.filter(pk=associated.pk).update(associated=race)
        logger.info(f"update {race.pk} associated race with {associated.pk}")
    return race


def _retrieve_race(race: RSRace, trophy: Trophy | None, flag: Flag | None) -> Race | None:
    league = _retrieve_league(race, db_race=None)
    try:
        return RaceService.get_closest_match(
            trophy=trophy,
            flag=flag,
            league=league,
            gender=race.gender,
            date=datetime.strptime(race.date, "%d/%m/%Y").date(),
        )
    except Race.DoesNotExist:
        return input_race(race.name)


def _retrieve_trophy_and_flag(race: RSRace) -> tuple[TrophyEdition, FlagEdition]:
    (trophy, trophy_edition), (flag, flag_edition) = CompetitionService.retrieve_competition(race.normalized_names)

    ddate = datetime.strptime(race.date, "%d/%m/%Y").date()
    if trophy and not trophy_edition:
        edition = TrophyService.infer_trophy_edition(trophy, str(race.gender), ddate.year)
        if not edition:
            edition = inquirer.text(f"race_id={race.race_id}::edition for trophy {race.league}:{trophy}", default=None)
        if edition:
            trophy_edition = int(edition)
        else:
            trophy = None
    if flag and not flag_edition:
        edition = FlagService.infer_flag_edition(flag, str(race.gender), ddate.year)
        if not edition:
            edition = inquirer.text(f"race_id={race.race_id}::edition for flag {race.league}:{flag}", default=None)
        if edition:
            flag_edition = int(edition)
        else:
            flag = None

    if not trophy and not flag:
        (trophy, trophy_edition), (flag, flag_edition) = input_trophy(race.name), input_flag(race.name)

    return (trophy, trophy_edition), (flag, flag_edition)


def _retrieve_league(race: RSRace, db_race: Race | None) -> League | None:
    if db_race:
        return db_race.league

    if race.league and not is_play_off(remove_parenthesis(race.name)):
        return LeagueService.get_by_name(race.league)

    return None
