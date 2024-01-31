import logging

from django.db.models import Q, QuerySet

from apps.participants.models import Participant
from apps.races.models import Race
from rscraping.data.functions import is_branch_club

logger = logging.getLogger(__name__)


def get_by_race(race: Race) -> QuerySet[Participant]:
    return Participant.objects.filter(race=race)


def get_participant_or_create(participant: Participant, maybe_branch: bool = False) -> tuple[bool, Participant]:
    q = Participant.objects.filter(
        club=participant.club,
        race=participant.race,
        gender=participant.gender,
        category=participant.category,
    )

    if maybe_branch:
        q = _add_branch_filters(q, participant)

    try:
        # check for multiple results and get the non-branch club
        q = q.exclude(club_name__endswith=" B").exclude(club_name__endswith=" C") if q.count() > 1 else q
        return False, q.get()
    except Participant.DoesNotExist:
        participant.save()

        logger.info(f"created:: {participant}")
        return True, participant


def _add_branch_filters(q: QuerySet, participant: Participant) -> QuerySet:
    if not participant.club_name:
        return q

    if not is_branch_club(participant.club_name) and not is_branch_club(participant.club_name, letter="C"):
        return q.exclude(Q(club_name__endswith=" B") | Q(club_name__endswith=" C"))

    if is_branch_club(participant.club_name):
        return q.filter(club_name__endswith=" B")
    if is_branch_club(participant.club_name, letter="C"):
        return q.filter(club_name__endswith=" C")

    return q
