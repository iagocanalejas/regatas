import logging

from django.db import connection
from django.db.models import Q, QuerySet

from apps.entities.models import Entity, League
from apps.participants.models import Participant
from apps.races.models import Race
from rscraping.data.checks import is_branch_club
from rscraping.data.constants import GENDER_ALL
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
    if raw_club_name:
        q = _add_branch_filters(q, raw_club_name)

    try:
        return q.get()
    except Participant.DoesNotExist:
        return None


def get_year_speeds_by_club(
    club: Entity | None,
    league: League | None,
    gender: str,
    branch_teams: bool,
    only_league_races: bool,
    normalize: bool,
) -> dict[int, list[float]]:
    gender_filter = (
        f"(p.gender = '{gender}' AND r.gender = '{gender}')"
        if only_league_races or league is not None
        else f"(p.gender = '{gender}' AND (r.gender = '{gender}' OR r.gender = '{GENDER_ALL}'))"
    )
    branch_filter = (
        "p.club_name LIKE '% B'"
        if branch_teams
        else "(p.club_name IS NULL OR p.club_name <> '% B')"
        if not league
        else ""
    )

    filters = (
        "NOT r.cancelled",
        "p.laps <> '{}'",
        "(extract(EPOCH FROM p.laps[cardinality(p.laps)])) > 0",  # Avoid division by zero
        "NOT EXISTS(SELECT * FROM penalty WHERE participant_id = p.id AND disqualification)",  # Avoid disqualifications
        gender_filter,
        branch_filter,
        f"p.club_id = {club.pk}" if club else "",
        "r.league_id IS NOT NULL" if only_league_races else "",
        f"r.league_id = {league.pk}" if league else "",
    )
    where_clause = " AND ".join([str(filter) for filter in filters if filter])
    speed_expression = "(p.distance / (extract(EPOCH FROM p.laps[cardinality(p.laps)]))) * 3.6"

    if normalize:
        raw_query = f"""
            WITH speeds_query AS (
                SELECT
                    extract(YEAR from date)::INTEGER as year,
                    CAST({speed_expression} AS DOUBLE PRECISION) as speed
                FROM participant p JOIN race r ON p.race_id = r.id
                WHERE {where_clause}
            )
            SELECT year, array_agg(speed) AS speeds
            FROM speeds_query
            WHERE speed BETWEEN (
                SELECT AVG(speed) - (2 * STDDEV_POP(speed))
                FROM speeds_query
            ) AND (
                SELECT AVG(speed) + (2 * STDDEV_POP(speed))
                FROM speeds_query
            )
            GROUP BY year
            ORDER BY year;
            """
    else:
        raw_query = f"""
            SELECT
                extract(YEAR from date)::INTEGER as year,
                array_agg(CAST({speed_expression} AS DOUBLE PRECISION)) as speeds
            FROM participant p JOIN race r ON p.race_id = r.id
            WHERE {where_clause}
            GROUP BY year
            ORDER BY year;
            """

    logger.debug(raw_query)

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        speeds = cursor.fetchall()

    return {year: speed for year, speed in speeds}


def is_same_participant(p1: Participant, p2: Participant | RSParticipant, club: Entity | None = None) -> bool:
    if isinstance(p2, RSParticipant):
        return club is not None and (
            p1.club == club
            and p1.gender == p2.gender
            and p1.category == p2.category
            and (p1.club_name is not None and is_branch_club(p1.club_name) == is_branch_club(p2.club_name))
        )
    return (
        p1.club == p2.club
        and p1.gender == p2.gender
        and p1.category == p2.category
        and (
            p1.club_name is not None
            and p2.club_name is not None
            and is_branch_club(p1.club_name) == is_branch_club(p2.club_name)
        )
    )


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
