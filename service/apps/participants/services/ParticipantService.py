import logging
from typing import List, Tuple

from django.db.models import QuerySet

from apps.participants.models import Participant

logger = logging.getLogger(__name__)


def get_by_race_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Participant]:
    queryset = Participant.objects.filter(race_id=race_id)
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return queryset


def get_participant_or_create(participant: Participant) -> Tuple[bool, Participant]:
    q = Participant.objects.filter(club=participant.club, race=participant.race)

    try:
        return False, q.get()
    except Participant.DoesNotExist:
        participant.save()

        logger.info(f'created:: {participant}')
        return True, participant
