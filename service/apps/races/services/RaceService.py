import logging

from django.db.models import Q, QuerySet

from apps.races.filters import RaceFilters
from apps.races.models import Race

logger = logging.getLogger(__name__)


def filter(
    queryset: QuerySet[Race],
    filters: dict,
    related: list[str] | None = None,
    prefetch: list[str] | None = None,
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


def get_by_race(race: Race) -> Race | None:
    q = Race.objects.filter(league=race.league) if race.league else Race.objects.filter(league__isnull=True)
    q = q.filter(trophy=race.trophy) if race.trophy else q.filter(trophy__isnull=True)
    q = q.filter(flag=race.flag) if race.flag else q.filter(flag__isnull=True)
    q = q.filter(date=race.date)

    try:
        return q.get()
    except Race.DoesNotExist:
        return None


def find_associated(race: Race, year: int, day: int) -> Race | None:
    try:
        match = Race.objects.get(
            Q(trophy=race.trophy) | Q(trophy_id__isnull=True),
            Q(trophy_edition=race.trophy_edition) | Q(trophy_edition__isnull=True),
            flag=race.flag,
            flag_edition=race.flag_edition,
            league=race.league,
            date__year=year,
            day=day,
        )
        return match
    except Race.DoesNotExist:
        return None
