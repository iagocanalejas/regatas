import logging
from typing import List, Tuple

from django.db.models import QuerySet
from rest_framework.generics import get_object_or_404

from apps.races.filters import RaceFilters
from apps.races.models import Race

logger = logging.getLogger(__name__)


def get_by_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> Race:
    queryset = Race.objects
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return get_object_or_404(queryset, pk=race_id)


def get_filtered(queryset: QuerySet[Race], filters: dict, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Race]:
    queryset = RaceFilters(queryset) \
        .set_filters(filters) \
        .set_keywords(filters.get('keywords', None)) \
        .set_sorting(filters.get('ordering', None)) \
        .build_query()

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
