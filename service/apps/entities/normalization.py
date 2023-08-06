from django.db.models import Q
from rscraping.data.normalization.clubs import normalize_club_name as rs_normalize_club_name, _KNOWN_SPONSORS

from ai_django.ai_core.utils.strings import whitespaces_clean
from apps.entities.models import Entity
from utils.choices import ENTITY_CLUB


def normalize_club_name(name: str) -> str:
    name = rs_normalize_club_name(name)
    name = remove_club_sponsor(name)

    return name


def remove_club_sponsor(name: str) -> str:
    if "-" in name:
        parts = name.split("-")
        maybe_club, maybe_sponsor = parts[0].strip(), parts[1].strip()

        # check if the first part is a club
        query = Entity.queryset_for_search().filter(
            Q(name__icontains=maybe_club) | Q(joined_names__icontains=maybe_club), type=ENTITY_CLUB
        )
        if not maybe_club or not query.exists():
            maybe_club = None

        # check if the second part is a club
        query = Entity.queryset_for_search().filter(
            Q(name__icontains=maybe_sponsor) | Q(joined_names__icontains=maybe_sponsor), type=ENTITY_CLUB
        )
        if not maybe_sponsor or not query.exists() or maybe_sponsor in _KNOWN_SPONSORS:
            maybe_sponsor = None

        if all(i is None for i in [maybe_club, maybe_sponsor]):
            return name

        name = " - ".join(i for i in [maybe_club, maybe_sponsor] if i is not None)
    return whitespaces_clean(name)
