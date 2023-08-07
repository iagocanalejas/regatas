import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import inquirer
from rest_framework import serializers
from utils.exceptions import StopProcessing

from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService, LeagueService
from apps.participants.models import Participant, Penalty
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, TrophyService
from apps.schemas import MetadataBuilder
from apps.serializers import EntitySerializer, FlagSerializer, LeagueSerializer, TrophySerializer
from rscraping.data.functions import is_memorial
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

    if not trophy and not flag:
        raise StopProcessing(f"no trophy/flag found for {race.normalized_names}")

    if not race.url:
        raise StopProcessing(f"no datasource provided for race={race.name}")

    if trophy and not trophy_edition:
        trophy_edition = int(inquirer.text(f"Edition for trophy {trophy}: ", default=None))
    if flag and not flag_edition:
        flag_edition = int(inquirer.text(f"Edition for flag {flag}: ", default=None))

    organizer = _find_club(race.organizer) if race.organizer else None

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
        league=race.league and LeagueService.get_by_name(race.league),
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

    print(json.dumps(CommandRaceSerializer(new_race).data, indent=4, skipkeys=True, ensure_ascii=False))
    if not inquirer.confirm(f"Save new race for {race.name} in the database?", default=False):
        raise StopProcessing

    new_race.save()
    return new_race


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
            gender=p.gender,
            category=p.category,
        )
        for p in participants
    ]

    serialized_participants = CommandParticipantSerializer(new_participants, many=True).data
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
        return None
    except Entity.MultipleObjectsReturned:
        raise StopProcessing(f"multiple clubs found for {name=}")


class CommandRaceSerializer(serializers.ModelSerializer):
    trophy = TrophySerializer()
    flag = FlagSerializer()
    league = LeagueSerializer(allow_null=True)
    organizer = EntitySerializer(allow_null=True)

    class Meta:
        model = Race
        fields = (
            "id",
            "type",
            "modality",
            "day",
            "date",
            "cancelled",
            "trophy",
            "trophy_edition",
            "flag",
            "flag_edition",
            "league",
            "sponsor",
            "laps",
            "lanes",
            "town",
            "organizer",
            "metadata",
        )


class CommandParticipantSerializer(serializers.ModelSerializer):
    club = EntitySerializer()
    club_name = serializers.SerializerMethodField()

    # noinspection DuplicatedCode
    @staticmethod
    def get_club_name(participant: Participant) -> Optional[str]:
        extra = None
        if participant.club_name:
            extra = [e for e in ["B", "C", "D"] if e in participant.club_name.split()]
            extra = "".join(e for e in extra) if extra else None
        return f'{participant.club} "{extra}"' if extra else None

    class Meta:
        model = Participant
        fields = ("id", "laps", "lane", "series", "gender", "category", "distance", "club", "club_name")
