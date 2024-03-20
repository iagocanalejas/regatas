import logging

from django.db.models import QuerySet

from apps.races.filters import RaceFilters
from apps.races.models import Race
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


def get_race_or_none(
    ref_id: str,
    datasource: Datasource,
    day: int | None = None,
) -> Race | None:
    metadata: dict = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}

    filters: dict = {"metadata": [metadata]}
    if day:
        filters["day"] = day

    queryset = (
        RaceFilters(Race.objects)
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )

    logger.debug(f"trying to find {ref_id=} in {datasource=}")
    try:
        return queryset.get()
    except Race.DoesNotExist:
        return None


def get_datasource(
    race: Race,
    datasource: Datasource,
    ref_id: str,
    sheet_id: str | None = None,
    sheet_name: str | None = None,
) -> list[dict]:
    datasources = race.metadata["datasource"]
    matches = [d for d in datasources if d["datasource_name"] == datasource.value.lower() and d["ref_id"] == ref_id]
    if datasource == Datasource.TABULAR:
        assert sheet_id is not None
        matches = [d for d in matches if d["values"]["sheet_id"] == sheet_id]
        if sheet_name:
            matches = [d for d in matches if d["values"]["sheet_name"] == sheet_name]
    return matches


def exists(
    ref_id: str,
    datasource: Datasource,
    *_,
    day: int | None = None,
    sheet_id: str | None = None,
    sheet_name: str | None = None,
) -> bool:
    metadata: dict = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}
    if datasource == Datasource.TABULAR and sheet_id:
        metadata["values"] = {"sheet_id": sheet_id}
    if datasource == Datasource.TABULAR and sheet_name:
        metadata["values"]["sheet_name"] = sheet_name

    filters: dict = {"metadata": [metadata]}
    if day:
        filters["day"] = day

    queryset = (
        RaceFilters(Race.objects)
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )
    return queryset.exists()


def get_races_by_datasource(datasource: Datasource) -> QuerySet[Race]:
    filters: dict = {"metadata": [{"datasource_name": datasource.value.lower()}]}
    queryset = RaceFilters(Race.objects).set_filters(filters).build_query()
    logger.debug(f"retrieving races for {datasource=}")
    return queryset.all()
