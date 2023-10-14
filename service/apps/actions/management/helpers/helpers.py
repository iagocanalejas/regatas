import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import inquirer
from django.core.exceptions import ValidationError
from django.db.models import Q
from utils.exceptions import StopProcessing

from apps.actions.serializers import ParticipantSerializer, RaceSerializer
from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService, LeagueService
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from pyutils.strings import remove_conjunctions, remove_parenthesis
from rscraping.data.functions import is_memorial, is_play_off
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


def preload_participants(participants: List[RSParticipant]) -> Dict[str, Entity]:
    logger.info(f"preloading {len(participants)} clubs")
    clubs = {p.participant: _find_club(normalize_club_name(p.participant)) for p in participants}
    if any(not c for c in clubs.values()):
        not_found = {k: v for k, v in clubs.items() if not v}
        raise StopProcessing(f"no club found clubs={not_found}")
    return {k: v for k, v in clubs.items() if v}


def save_race_from_scraped_data(race: RSRace, datasource: Datasource, allow_merges: bool = False) -> Race:
    race.participants = []

    logger.info("preloading trophy & flag")
    trophy, trophy_edition = _find_trophy(race.normalized_names)
    flag, flag_edition = _find_flag(race.normalized_names)

    if not trophy and not flag:
        (trophy, trophy_edition), (flag, flag_edition) = _try_manual_input(race.name)

    if not race.url:
        raise StopProcessing(f"no datasource provided for {race.race_id}::{race.name}")

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
        raise StopProcessing(f"no trophy/flag found for {race.race_id}::{race.normalized_names}")

    logger.info("preloading organizer")
    organizer = _find_club(race.organizer) if race.organizer else None

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


def save_participants_from_scraped_data(
    race: Race,
    participants: List[RSParticipant],
    preloaded_clubs: Dict[str, Entity],
    allow_merges: bool = False,
) -> List[Participant]:
    def is_same_participant(p: RSParticipant, p1: Participant) -> bool:
        return preloaded_clubs[p.participant] == p1.club and p.category == p1.category and p.gender == p1.gender

    if allow_merges:  # TODO: maybe this should also run if 'use_db'
        existing_participants = ParticipantService.get_by_race(race=race)
        logger.info(f"{len(existing_participants)} participants found in the database")
        participants = [p for p in participants if not any(is_same_participant(p, p1) for p1 in existing_participants)]

    logger.info(f"{len(participants)} participants will be added to the database")
    new_participants = [
        Participant(
            club_name=p.club_name,
            club=preloaded_clubs[p.participant],
            race=race,
            distance=p.distance,
            laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in p.laps],
            lane=p.lane,
            series=p.series,
            handicap=datetime.strptime(p.handicap, "%M:%S.%f").time() if p.handicap else None,
            gender=p.gender,
            category=p.category,
        )
        for p in participants
    ]

    serialized_participants = ParticipantSerializer(new_participants, many=True).data
    for index, serialized_participant in enumerate(serialized_participants):
        print(json.dumps(serialized_participant, indent=4, skipkeys=True, ensure_ascii=False))
        if not inquirer.confirm(f"Save new participant for {race=} in the database?", default=False):
            continue

        new_participants[index].save()

        if participants[index].disqualified:
            logger.info("creating disqualification penalty")
            Penalty(disqualification=True, participant=new_participants[index]).save()
    return new_participants


def _save_race_from_scraped_data(race: Race, associated: Optional[Race]) -> Race:
    if not inquirer.confirm(f"Save new race for {race.name} to the database?", default=False):
        raise StopProcessing

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
    if not inquirer.confirm(
        f"Found matching race in the database for race {race.name}. Merge both races?",
        default=False,
    ):
        raise StopProcessing

    if not any(is_current_datasource(d) for d in db_race.metadata["datasource"]):
        db_race.metadata["datasource"].append(race.metadata["datasource"][0])

    print(json.dumps(RaceSerializer(db_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    if not inquirer.confirm(f"Save new race for {race.name}?", default=False):
        raise StopProcessing

    db_race.save()
    logger.info(f"{db_race.pk} updated with new data")
    return db_race


def _infer_edition(race: RSRace, trophy: Optional[Trophy] = None, flag: Optional[Flag] = None) -> Optional[int]:
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


def _find_trophy(names: List[Tuple[str, Optional[int]]]) -> Tuple[Optional[Trophy], Optional[int]]:
    for name, edition in names:
        if len(names) > 1 and is_memorial(name):
            continue
        try:
            return TrophyService.get_closest_by_name(name), edition
        except Trophy.DoesNotExist:
            continue
    return None, None


def _find_flag(names: List[Tuple[str, Optional[int]]]) -> Tuple[Optional[Flag], Optional[int]]:
    for name, edition in names:
        if len(names) > 1 and is_memorial(name):
            continue
        try:
            return FlagService.get_closest_by_name(name), edition
        except Flag.DoesNotExist:
            continue
    return None, None


def _find_club(name: str) -> Optional[Entity]:
    try:
        return EntityService.get_closest_club_by_name(name)
    except Entity.DoesNotExist:
        try:
            return EntityService.get_closest_club_by_name(remove_conjunctions(name))
        except Entity.DoesNotExist:
            return None
    except Entity.MultipleObjectsReturned:
        raise StopProcessing(f"multiple clubs found for {name=}")


def _try_manual_input(name: str) -> Tuple[Tuple[Optional[Trophy], Optional[int]], Tuple[Optional[Flag], Optional[int]]]:
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
