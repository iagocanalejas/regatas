import logging

from django.db import connection
from django.db.models import Q, QuerySet

from apps.entities.models import Entity, League
from apps.participants.models import Participant, Penalty
from apps.races.models import Flag, Race
from rscraping.data.checks import is_branch_club
from rscraping.data.constants import CATEGORY_ALL, GENDER_ALL
from rscraping.data.models import Participant as RSParticipant

logger = logging.getLogger(__name__)


def get_by_race(race: Race) -> QuerySet[Participant]:
    return Participant.objects.filter(race=race)


def get_by_race_and_filter_by(
    race: Race,
    club: Entity,
    gender: str,
    category: str,
    raw_club_name: str | None = None,
) -> Participant | None:
    q = get_by_race(race).filter(club=club, category=category, gender=gender)
    if q.count() > 1 and raw_club_name and race.league is None:
        q = _add_branch_filters(q, raw_club_name)

    try:
        return q.get()
    except Participant.DoesNotExist:
        return None


def get_penalties(participant: Participant) -> QuerySet:
    return Penalty.objects.filter(participant=participant)


def is_same_participant(p1: Participant, p2: Participant | RSParticipant, club: Entity | None = None) -> bool:
    if isinstance(p2, RSParticipant):
        return club is not None and (
            p1.club == club
            and p1.gender == p2.gender
            and p1.category == p2.category
            and (p1.club_names and any(is_branch_club(e) for e in p1.club_names) and is_branch_club(p2.club_name))
        )
    return (
        p1.club == p2.club
        and p1.gender == p2.gender
        and p1.category == p2.category
        and (
            p1.club_names
            and p2.club_names
            and any(is_branch_club(e) for e in p1.club_names)
            and any(is_branch_club(e) for e in p2.club_names)
        )
    )


def get_year_speeds_filtered_by(
    club: Entity | None,
    league: League | None,
    flag: Flag | None,
    gender: str,
    category: str,
    day: int,
    branch_teams: bool,
    only_league_races: bool,
    normalize: bool,
) -> dict[int, list[float]]:
    subquery_where_clause = _get_speed_filters(
        club=club,
        league=league,
        flag=flag,
        gender=gender,
        category=category,
        day=day,
        branch_teams=branch_teams,
        only_league_races=only_league_races,
    )
    speed_expression = "(p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6"
    where_clause = ""

    if normalize:
        where_clause = """
            WHERE speed BETWEEN (
                SELECT AVG(speed) - (2 * STDDEV_POP(speed))
                FROM speeds_query
            ) AND (
                SELECT AVG(speed) + (2 * STDDEV_POP(speed))
                FROM speeds_query
            )
        """

    raw_query = f"""
        WITH speeds_query AS (
            SELECT
                extract(YEAR from date)::INTEGER as year,
                CAST({speed_expression} AS DOUBLE PRECISION) as speed
            FROM participant p JOIN race r ON p.race_id = r.id
            WHERE {subquery_where_clause}
            ORDER BY r.date, speed DESC
        )
        SELECT year, array_agg(speed) AS speeds
        FROM speeds_query
        {where_clause}
        GROUP BY year
        ORDER BY year;
    """

    logger.debug(raw_query)

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        speeds = cursor.fetchall()

    return {year: speed for year, speed in speeds}


def get_nth_speed_filtered_by(
    index: int,  # the index is one-based as postgresql does not support zero-based arrays
    club: Entity | None,
    league: League | None,
    gender: str,
    category: str,
    year: int,
    day: int,
    branch_teams: bool,
    only_league_races: bool,
    normalize: bool,
) -> list[float]:
    subquery_where_clause = _get_speed_filters(
        club=club,
        league=league,
        flag=None,
        gender=gender,
        category=category,
        day=day,
        branch_teams=branch_teams,
        only_league_races=only_league_races,
    )
    subquery_where_clause += f" AND extract(YEAR from r.date) = {year}"
    speed_expression = "(p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6"
    where_clause = ""

    if normalize:
        where_clause = """
            WHERE speed BETWEEN (
                SELECT AVG(speed) - (2 * STDDEV_POP(speed))
                FROM speeds_query
            ) AND (
                SELECT AVG(speed) + (2 * STDDEV_POP(speed))
                FROM speeds_query
            )
        """

    raw_query = f"""
        WITH speeds_query AS (
            SELECT
                p.race_id,
                CAST({speed_expression} AS DOUBLE PRECISION) as speed
            FROM participant p JOIN race r ON p.race_id = r.id
            WHERE {subquery_where_clause}
            ORDER BY r.date
        )
        SELECT race_id, (array_agg(speed ORDER BY speed DESC))[{index}] AS speed
        FROM speeds_query
        {where_clause}
        GROUP BY race_id
        HAVING array_length(array_agg(speed), 1) >= {index};
    """

    logger.debug(raw_query)

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        speeds = cursor.fetchall()

    return [speed for _, speed in speeds]


def _get_speed_filters(
    club: Entity | None,
    league: League | None,
    flag: Flag | None,
    gender: str,
    category: str,
    day: int,
    branch_teams: bool,
    only_league_races: bool,
) -> str:
    gender_filter = (
        f"(p.gender = '{gender}' AND r.gender = '{gender}')"
        if only_league_races or league is not None
        else f"(p.gender = '{gender}' AND (r.gender = '{gender}' OR r.gender = '{GENDER_ALL}'))"
    )
    category_filter = (
        f"(p.category = '{category}' AND r.category = '{category}')"
        if only_league_races or league is not None
        else f"(p.category = '{category}' AND (r.category = '{category}' OR r.category = '{CATEGORY_ALL}'))"
    )
    branch_filter = (
        "EXISTS(SELECT 1 FROM unnest(p.club_names) AS club_name WHERE club_name LIKE '% B')"
        if branch_teams
        else "(p.club_names = '{}' OR NOT EXISTS(SELECT 1 FROM unnest(p.club_names) AS club_name WHERE club_name LIKE '% B'))"  # noqa: E501
        if not league and not flag
        else ""
    )

    filters = (
        "NOT r.cancelled",
        f"r.day = {day}",
        "p.laps <> '{}'",
        "NOT p.retired",
        "NOT p.guest",
        "NOT p.absent",
        "(extract(EPOCH FROM p.laps[cardinality(p.laps)])) > 0",  # Avoid division by zero
        "NOT EXISTS(SELECT * FROM penalty WHERE participant_id = p.id AND disqualification)",  # Avoid disqualifications
        gender_filter,
        category_filter,
        branch_filter,
        f"p.club_id = {club.pk}" if club else "",
        "r.league_id IS NOT NULL" if only_league_races else "",
        f"r.league_id = {league.pk}" if league else "",
        f"r.flag_id = {flag.pk}" if flag else "",
    )
    return " AND ".join([str(filter) for filter in filters if filter])


def _add_branch_filters(q: QuerySet, club_name: str | None) -> QuerySet:
    if not club_name:
        return q

    if not is_branch_club(club_name) and not is_branch_club(club_name, letter="C"):
        return q.exclude(Q(club_name__endswith=" B") | Q(club_name__endswith=" C"))

    if is_branch_club(club_name):
        return q.filter(club_name__endswith=" B")
    if is_branch_club(club_name, letter="C"):
        return q.filter(club_name__endswith=" C")

    return q
