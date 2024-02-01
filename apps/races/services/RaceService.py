import logging
from datetime import date

from django.db.models import Q, QuerySet

from apps.entities.models import League
from apps.entities.services import LeagueService
from apps.races.filters import RaceFilters
from apps.races.models import Flag, Race, Trophy
from apps.races.services import CompetitionService
from rscraping.data.constants import GENDER_ALL
from rscraping.data.functions import is_play_off

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
    """
    matches = Race.objects.filter(date__year=year, day=day)
    if race.league:
        matches = matches.filter(league__isnull=True) if is_play_off(race.name) else matches.filter(league=race.league)
    if race.flag:
        matches = matches.filter(flag=race.flag, flag_edition=race.flag_edition)
    if race.trophy:
        matches = matches.filter(trophy=race.trophy, trophy_edition=race.trophy_edition)
    try:
        return matches.get()
    except Race.DoesNotExist:
        return None


def get_closest_match_by_name_or_none(
    names: list[str],
    league: League | str | None,
    gender: str | None,
    date: date,
    day: int = 1,
) -> Race | None:
    try:
        return get_closest_match_by_name(names=names, league=league, gender=gender, date=date, day=day)
    except Race.DoesNotExist:
        return None


def get_closest_match_by_name(
    names: list[str],
    league: League | str | None,
    gender: str | None,
    date: date,
    day: int = 1,
) -> Race:
    trophy, flag = CompetitionService.get_competition_or_none(names)
    if not trophy and not flag:
        raise Race.DoesNotExist
    if league and isinstance(league, str):
        league = LeagueService.get_by_name(league)
    assert league is None or isinstance(league, League)
    return get_closest_match(trophy=trophy, flag=flag, league=league, gender=gender, date=date, day=day)


def get_closest_match(
    trophy: Trophy | None,
    flag: Flag | None,
    league: League | None,
    gender: str | None,
    date: date,
    day: int = 1,
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
    races = Race.objects.filter(Q(gender=gender) | Q(gender=GENDER_ALL), date=date, day=day)
    if trophy:
        races = races.filter(trophy=trophy)
    if flag:
        races = races.filter(flag=flag)
    if league:
        races = races.filter(league=league)
    return races.get()