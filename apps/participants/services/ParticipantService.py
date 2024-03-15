import logging

from django.db.models import Q, QuerySet

from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.races.models import Race
from rscraping.data.functions import is_branch_club
from rscraping.data.models import Participant as RSParticipant

logger = logging.getLogger(__name__)


def get_by_race(race: Race) -> QuerySet[Participant]:
    return Participant.objects.filter(race=race)


def get_by_race_and_filter_by(
    race: Race,
    club: Entity,
    category: str,
    gender: str,
    raw_club_name: str | None = None,
) -> Participant | None:
    q = get_by_race(race).filter(club=club, category=category, gender=gender)
    if raw_club_name:
        q = _add_branch_filters(q, raw_club_name)

    try:
        return q.get()
    except Participant.DoesNotExist:
        return None


def get_participant_or_create(participant: Participant, maybe_branch: bool = False) -> tuple[bool, Participant]:
    q = Participant.objects.filter(
        club=participant.club,
        race=participant.race,
        gender=participant.gender,
        category=participant.category,
    )

    if maybe_branch:
        q = _add_branch_filters(q, participant.club_name)

    try:
        # check for multiple results and get the non-branch club
        q = q.exclude(club_name__endswith=" B").exclude(club_name__endswith=" C") if q.count() > 1 else q
        return False, q.get()
    except Participant.DoesNotExist:
        participant.save()

        logger.info(f"created:: {participant}")
        return True, participant


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
