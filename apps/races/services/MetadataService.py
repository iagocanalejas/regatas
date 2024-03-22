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
    queryset = RaceFilters(Race.objects).set_filters(filters).build_query()

    return queryset.all()


def get_race_or_none(datasource: Datasource, ref_id: str, day: int | None = None) -> Race | None:
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


def exists(
    datasource: Datasource,
    ref_id: str,
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


def get_datasource_from_race(
    datasource: Datasource,
    race: Race,
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
