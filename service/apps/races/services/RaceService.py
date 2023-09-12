import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import QuerySet
from rest_framework.generics import get_object_or_404
from utils.choices import GENDER_FEMALE, GENDER_MALE

from apps.races.filters import RaceFilters
from apps.races.models import Race
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


def get_by_id(
    race_id: int,
    related: Optional[List[str]] = None,
    prefetch: Optional[List[str]] = None,
) -> Race:
    queryset = Race.objects
    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset
    return get_object_or_404(queryset, pk=race_id)


def get_filtered(
    queryset: QuerySet[Race],
    filters: dict,
    related: Optional[List[str]] = None,
    prefetch: Optional[List[str]] = None,
) -> QuerySet[Race]:
    queryset = (
        RaceFilters(queryset)
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )

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

        logger.info(f"created:: {race}")
        return True, race


def get_by_datasource(
    ref_id: str,
    datasource: Datasource,
    gender: Optional[str] = None,
    day: Optional[int] = None,
) -> Optional[Race]:
    metadata: Dict[str, Dict[str, str] | str] = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}
    if gender and gender in [GENDER_MALE, GENDER_FEMALE]:
        metadata["values"] = {"gender": gender}

    filters: Dict[str, Any] = {"metadata": [metadata]}
    if day:
        filters["day"] = day

    try:
        return get_filtered(queryset=Race.objects, filters=filters, prefetch=["participants"]).get()
    except Race.DoesNotExist:
        return None
