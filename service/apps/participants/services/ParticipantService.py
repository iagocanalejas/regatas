import logging
from typing import List, Tuple

from django.db.models import QuerySet, Q

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_conjunctions, remove_symbols
from apps.participants.models import Participant
from apps.races.filters import build_base_filters, build_keyword_filter
from utils.checks import is_branch_club

logger = logging.getLogger(__name__)


def get_by_race_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Participant]:
    queryset = Participant.objects.filter(race_id=race_id)
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return queryset


def get_filtered(queryset: QuerySet[Participant],
                 filters: dict,
                 related: List[str] = None,
                 prefetch: List[str] = None) -> QuerySet[Participant]:
    queryset = queryset.filter(**build_base_filters(filters, prefix='race'))
    if 'keywords' in filters:
        keywords = whitespaces_clean(remove_conjunctions(remove_symbols(filters['keywords'])))
        queryset = queryset.filter(build_keyword_filter(keywords, prefix='race'))

    queryset = queryset.order_by('race__date')

    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset

    return queryset.all()


def get_participant_or_create(participant: Participant, maybe_branch: bool = False) -> Tuple[bool, Participant]:
    q = Participant.objects.filter(
        club=participant.club,
        race=participant.race,
        gender=participant.gender,
        category=participant.category,
    )

    if maybe_branch:
        q = _add_branch_filters(q, participant)

    try:
        # check for multiple results and get the non-branch club
        q = q.exclude(club_name__endswith=' B').exclude(club_name__endswith=' C') if q.count() > 1 else q
        return False, q.get()
    except Participant.DoesNotExist:
        participant.save()

        logger.info(f'created:: {participant}')
        return True, participant


def _add_branch_filters(q: QuerySet, participant: Participant) -> QuerySet:
    if not is_branch_club(participant.club_name) and not is_branch_club(participant.club_name, letter='C'):
        return q.exclude(Q(club_name__endswith=' B') | Q(club_name__endswith=' C'))

    if is_branch_club(participant.club_name):
        return q.filter(club_name__endswith=' B')
    if is_branch_club(participant.club_name, letter='C'):
        return q.filter(club_name__endswith=' C')
