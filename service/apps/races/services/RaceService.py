import logging
from typing import List, Tuple

from django.db.models import QuerySet, Q
from rest_framework.generics import get_object_or_404

from ai_django.ai_core.utils.strings import remove_conjunctions, remove_symbols, whitespaces_clean
from apps.races.models import Race

logger = logging.getLogger(__name__)


def get_by_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> Race:
    queryset = Race.objects
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return get_object_or_404(queryset, pk=race_id)


def get_filtered(queryset: QuerySet[Race], filters: dict, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Race]:
    if 'year' in filters:
        queryset = queryset.filter(date__year=filters['year'])
    if 'trophy' in filters:
        queryset = queryset.filter(trophy=filters['trophy'])
    if 'flag' in filters:
        queryset = queryset.filter(flag=filters['flag'])
    if 'league' in filters:
        queryset = queryset.filter(league=filters['league'])
    if 'participant_club' in filters:
        queryset = queryset.filter(participant__club=filters['participant_club'])
    if 'metadata' in filters:
        queryset = queryset.filter(metadata__datasource__contains=filters['metadata'])
    if 'keywords' in filters:
        keywords = whitespaces_clean(remove_conjunctions(remove_symbols(filters['keywords'])))
        queryset = queryset.filter(
            Q(trophy__isnull=False, trophy__name__unaccent__icontains=keywords)
            | Q(flag__isnull=False, flag__name__unaccent__icontains=keywords)
            | Q(league__isnull=False, league__name__unaccent__icontains=keywords)
            | Q(sponsor__isnull=False, sponsor__unaccent__icontains=keywords) | Q(town__isnull=False, town__unaccent__icontains=keywords)
        )

    queryset = queryset.order_by('date')

    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset

    return queryset.all()


def get_race_or_create(race: Race) -> Tuple[bool, Race]:
    # try to find a matching existing race
    q = Race.objects.filter(league=race.league) if race.league else Race.objects.filter(league__isnull=True)
    q = q.filter(trophy=race.trophy) if race.trophy else q.filter(trophy__isnull=True)
    q = q.filter(flag=race.flag) if race.flag else q.filter(flag__isnull=True)
    q = q.filter(date=race.date)

    try:
        return False, q.get()
    except Race.DoesNotExist:
        race.save()

        logger.info(f'created:: {race}')
        return True, race
