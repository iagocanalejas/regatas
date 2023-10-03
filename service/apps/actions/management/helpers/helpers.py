import json
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
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, TrophyService
from apps.schemas import MetadataBuilder
from pyutils.strings import remove_conjunctions, remove_parenthesis
from rscraping.data.functions import is_memorial, is_play_off
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace


def preload_participants(participants: List[RSParticipant]) -> Dict[str, Entity]:
    clubs = {p.participant: _find_club(normalize_club_name(p.participant)) for p in participants}
    if any(not c for c in clubs.values()):
        not_found = {k: v for k, v in clubs.items() if not v}
        raise StopProcessing(f"no club found clubs={not_found}")
    return {k: v for k, v in clubs.items() if v}


def save_race_from_scraped_data(race: RSRace, datasource: Datasource) -> Race:
    race.participants = []

    trophy, trophy_edition = _find_trophy(race.normalized_names)
    flag, flag_edition = _find_flag(race.normalized_names)

    if not trophy and not flag:
        (trophy, trophy_edition), (flag, flag_edition) = _try_manual_input(race.name)

    if not race.url:
        raise StopProcessing(f"no datasource provided for {race.race_id}::{race.name}")

    if trophy and not trophy_edition:
        edition = inquirer.text(f"race_id={race.race_id}::Edition for trophy {race.league}:{trophy}", default=None)
        if edition:
            trophy_edition = int(edition)
        else:
            trophy = None
    if flag and not flag_edition:
        edition = inquirer.text(f"race_id={race.race_id}::Edition for flag {race.league}:{flag}", default=None)
        if edition:
            flag_edition = int(edition)
        else:
            flag = None

    if not trophy and not flag:
        raise StopProcessing(f"no trophy/flag found for {race.race_id}::{race.normalized_names}")

    organizer = _find_club(race.organizer) if race.organizer else None
    league = (
        LeagueService.get_by_name(race.league)
        if race.league and not is_play_off(remove_parenthesis(race.name))
        else None
    )

    associated = _find_associated(
        trophy_id=trophy.pk if trophy else None,
        trophy_edition=trophy_edition,
        flag_id=flag.pk if flag else None,
        flag_edition=flag_edition,
        league_id=league.pk if league else None,
        year=datetime.strptime(race.date, "%d/%m/%Y").date().year,
        day=2 if race.day == 1 else 2,
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
    if not inquirer.confirm(f"Save new race for {race.name} to the database?", default=False):
        raise StopProcessing

    try:
        new_race.save()
        if associated and inquirer.confirm(f"Link new race {race.name} with associated {associated.name}"):
            Race.objects.filter(pk=new_race.pk).update(associated=associated)
            Race.objects.filter(pk=associated.pk).update(associated=new_race)
        return new_race
    except ValidationError as e:
        if race.day == 1 and inquirer.confirm("Race already in DB. Is this race a second day?"):
            race.day = 2
            return save_race_from_scraped_data(race, datasource=datasource)
        raise e


def save_participants_from_scraped_data(
    race: Race, participants: List[RSParticipant], preloaded_clubs: Dict[str, Entity]
) -> List[Participant]:
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
            print("creating disqualification penalty")
            Penalty(disqualification=True, participant=new_participants[index]).save()
    return new_participants


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


def _find_associated(
    trophy_id: Optional[int],
    trophy_edition: Optional[int],
    flag_id: Optional[int],
    flag_edition: Optional[int],
    league_id: Optional[int],
    year: int,
    day: int,
) -> Optional[Race]:
    try:
        match = Race.objects.get(
            Q(trophy_id=trophy_id) | Q(trophy_id__isnull=True),
            Q(trophy_edition=trophy_edition) | Q(trophy_edition__isnull=True),
            flag_id=flag_id,
            flag_edition=flag_edition,
            league_id=league_id,
            date__year=year,
            day=day,
        )
        return match
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
