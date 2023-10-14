import logging
from typing import Dict, Optional

from apps.races.filters import RaceFilters
from apps.races.models import Race
from rscraping.data.constants import GENDER_FEMALE, GENDER_MALE
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


def get_race(
    ref_id: str,
    datasource: Datasource,
    gender: Optional[str] = None,
    day: Optional[int] = None,
) -> Optional[Race]:
    metadata: Dict = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}
    if gender and gender in [GENDER_MALE, GENDER_FEMALE]:
        metadata["values"] = {"gender": gender}

    filters: Dict = {"metadata": [metadata]}
    if day:
        filters["day"] = day

    queryset = (
        RaceFilters(Race.objects)
        .set_filters(filters)
        .set_keywords(filters.get("keywords", None))
        .set_sorting(filters.get("ordering", None))
        .build_query()
    )

    logger.debug(f"Trying to find {ref_id=} in {datasource=}")
    try:
        return queryset.get()
    except Race.DoesNotExist:
        return None


def exists(ref_id: str, datasource: Datasource, gender: Optional[str] = None, day: Optional[int] = None) -> bool:
    metadata: Dict = {"ref_id": ref_id, "datasource_name": datasource.value.lower()}
    if gender and gender in [GENDER_MALE, GENDER_FEMALE]:
        metadata["values"] = {"gender": gender}

    filters: Dict = {"metadata": [metadata]}
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