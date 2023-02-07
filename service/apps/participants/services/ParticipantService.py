import logging
from typing import List, Tuple

from django.db.models import QuerySet

from apps.participants.models import Participant
from utils.checks import is_branch_club

logger = logging.getLogger(__name__)


def get_by_race_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Participant]:
    queryset = Participant.objects.filter(race_id=race_id)
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return queryset


def get_participant_or_create(participant: Participant, maybe_branch: bool = False) -> Tuple[bool, Participant]:
    q = Participant.objects.filter(
        club=participant.club,
        race=participant.race,
        gender=participant.gender,
        category=participant.category,
    )

    # filter for B and C branch teams
    if maybe_branch:
        if is_branch_club(participant.club_name):
            q = q.filter(club_name__endswith=' B')
        if is_branch_club(participant.club_name, letter='C'):
            q = q.filter(club_name__endswith=' C')

    try:
        # check for multiple results and get the non-branch club
        q = q.exclude(club_name__endswith=' B').exclude(club_name__endswith=' C') if q.count() > 1 else q
        return False, q.get()
    except Participant.DoesNotExist:
        participant.save()

        logger.info(f'created:: {participant}')
        return True, participant
