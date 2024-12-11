import logging

from django.db.models import QuerySet

from apps.races.filters import RaceFilters
from apps.races.models import Race
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


def get_races(datasource: Datasource, ref_id: str | None = None) -> QuerySet[Race]:
    metadata: dict = {"datasource_name": datasource.value.lower()}
    if ref_id:
        metadata["ref_id"] = ref_id

    filters: dict = {"metadata": [metadata]}
    queryset = RaceFilters(Race.objects.all()).set_filters(filters).build_query()

    return queryset.all()


def get_race_or_none(
    datasource: Datasource,
    ref_id: str,
    day: int | None = None,
    related: list[str] | None = None,
    prefetch: list[str] | None = None,
) -> Race | None:
    metadata: dict = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}

    filters: dict = {"metadata": [metadata]}
    if day:
        filters["day"] = day

    queryset = (
        RaceFilters(Race.objects.all())
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )

    queryset = queryset.select_related(*related) if related else queryset
    queryset = queryset.prefetch_related(*prefetch) if prefetch else queryset

    logger.debug(f"trying to find {ref_id=} in {datasource=}")
    try:
        return queryset.get()
    except Race.DoesNotExist:
        return None


def exists(
    datasource: Datasource,
    ref_id: str,
    *_,
    day: int | None = None,
) -> bool:
    filters: dict = {"metadata": [{"ref_id": ref_id, "datasource_name": datasource.value.lower()}]}
    if day:
        filters["day"] = day

    queryset = (
        RaceFilters(Race.objects.all())
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )
    return queryset.exists()
