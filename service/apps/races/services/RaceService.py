import logging
from typing import List, Tuple

from django.db.models import QuerySet
from rest_framework.generics import get_object_or_404

from ai_django.ai_core.utils.strings import remove_conjunctions, remove_symbols, whitespaces_clean
from apps.races.filters import build_base_filters, build_keyword_filter
from apps.races.models import Race

logger = logging.getLogger(__name__)


def get_by_id(race_id: int, related: List[str] = None, prefetch: List[str] = None) -> Race:
    queryset = Race.objects
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return get_object_or_404(queryset, pk=race_id)


def get_filtered(queryset: QuerySet[Race], filters: dict, related: List[str] = None, prefetch: List[str] = None) -> QuerySet[Race]:
    queryset = queryset.filter(**build_base_filters(filters))
    if 'participant' in filters:
        queryset = queryset.filter(participant__club_id=filters['participant'])
    if 'metadata' in filters:
        queryset = queryset.filter(metadata__datasource__contains=filters['metadata'])
    if 'keywords' in filters:
        keywords = whitespaces_clean(remove_conjunctions(remove_symbols(filters['keywords'])))
        queryset = queryset.filter(build_keyword_filter(keywords))

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
