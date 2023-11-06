import json
import logging
from datetime import datetime

import inquirer
from utils.exceptions import StopProcessing

from apps.actions.serializers import ParticipantSerializer
from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Race
from pyutils.strings import remove_conjunctions
from rscraping.data.models import Participant as RSParticipant

logger = logging.getLogger(__name__)


def save_participants_from_scraped_data(
    race: Race,
    participants: list[RSParticipant],
    preloaded_clubs: dict[str, Entity],
    allow_merges: bool = False,
) -> list[Participant]:
    participants = _merge_participants_if_needed(race, participants, preloaded_clubs, allow_merges)

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


def preload_participants(participants: list[RSParticipant]) -> dict[str, Entity]:
    """
    Preload club information for a list of participants.

    This function takes a list of participants, retrieves club information for each participant, and returns
    a dictionary mapping participant names to their respective clubs. If a club is not found for a participant,
    an exception is raised.

    Args:
        participants (List[RSParticipant]): A list of participants to preload club information for.

    Returns:
        Dict[str, Entity]: A dictionary mapping participant names to their respective clubs.

    Raises:
        StopProcessing: If a club is not found for one or more participants, this exception is raised.
    """
    logger.info(f"preloading {len(participants)} clubs")
    clubs = {p.participant: find_club(normalize_club_name(p.participant)) for p in participants}
    not_found = {name: club for name, club in clubs.items() if not club}
    if not_found:
        raise StopProcessing(f"clubs not found: {not_found}")
    return {name: club for name, club in clubs.items() if club}


def find_club(name: str, full_cleaned=False) -> Entity | None:
    try:
        return EntityService.get_closest_club_by_name(name)
    except Entity.MultipleObjectsReturned:
        raise StopProcessing(f"multiple clubs found for {name=}")
    except Entity.DoesNotExist:
        pass

    if full_cleaned:
        entity_id = inquirer.text(f"no entity found for {name}. Entity ID: ", default=None)
        if entity_id:
            return Entity.objects.get(id=entity_id)
        return None
    else:
        return find_club(remove_conjunctions(name), full_cleaned=True)


def _merge_participants_if_needed(
    race: Race,
    participants: list[RSParticipant],
    preloaded_clubs: dict[str, Entity],
    allow_merges: bool = False,
) -> list[RSParticipant]:
    if not allow_merges:  # TODO: maybe this should also run if 'use_db'
        return participants

    def is_same_participant(p: RSParticipant, p1: Participant) -> bool:
        return preloaded_clubs[p.participant] == p1.club and p.category == p1.category and p.gender == p1.gender

    existing_participants = ParticipantService.get_by_race(race=race)
    logger.info(f"{len(existing_participants)} participants found in the database")
    return [p for p in participants if not any(is_same_participant(p, p1) for p1 in existing_participants)]
