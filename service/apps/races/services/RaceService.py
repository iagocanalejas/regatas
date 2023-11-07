import logging
from datetime import date

from django.db.models import Q, QuerySet
from utils.choices import GENDER_ALL

from apps.entities.models import League
from apps.races.filters import RaceFilters
from apps.races.models import Flag, Race, Trophy

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


def get_analogous_or_none(race: Race, year: int, day: int) -> Race | None:
    """
    Retrieve an analogous Race based on the provided race's attributes.

    Args:
        race (Race): The reference Race object.
        year (int): The year for which you want to find an analogous race.
        day (int): The day of the year for which you want to find an analogous race.

    Returns: Race | None: The analogous Race object if found, or None if no analogous race is found.

    Note:
    The function searches for an analogous race based on the following criteria:
    - Same Trophy or no Trophy
    - Same Trophy Edition or no Trophy Edition
    - Same Flag
    - Same Flag Edition
    - Same League
    - Matching year and day.

    If an analogous race is not found, the function returns None.
    """
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


def get_closest_match(
    trophy: Trophy | None,
    flag: Flag | None,
    league: League | None,
    gender: str | None,
    date: date,
) -> Race:
    """
    Retrieve the closest matching Race for a given combination of given parameters.

    Args:
        trophy (Trophy | None): The Trophy object or None.
        flag (Flag | None): The Flag object or None.
        league (League | None): The League object or None.
        gender (str | None): The gender associated with the race or None.
        date (date): The date of the race.

    Returns: Race: The closest matching Race object that meets the specified criteria.
    """
    races = Race.objects.filter(Q(gender=gender) | Q(gender=GENDER_ALL), date=date)
    if trophy:
        races = races.filter(Q(trophy__isnull=True) | Q(trophy=trophy))
    if flag:
        races = races.filter(Q(flag__isnull=True) | Q(flag=flag))
    if league:
        races = races.filter(Q(league__isnull=True) | Q(league=league))
    return races.get()
