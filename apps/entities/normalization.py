from django.db.models import Q

from apps.entities.models import Entity
from apps.utils.choices import ENTITY_CLUB
from pyutils.shortcuts import all_none
from pyutils.strings import whitespaces_clean
from rscraping.data.normalization.clubs import _KNOWN_SPONSORS
from rscraping.data.normalization.clubs import normalize_club_name as rs_normalize_club_name


def normalize_club_name(name: str) -> str:
    name = rs_normalize_club_name(name)
    name = remove_club_sponsor(name)

    return name


def remove_club_sponsor(name: str) -> str:
    if "-" in name:
        parts = name.split("-")
        maybe_club, maybe_sponsor = parts[0].strip(), parts[1].strip()

        # check if the first part is a club
        query = Entity.queryset_for_search(include_deleted=True).filter(
            Q(name__icontains=maybe_club) | Q(joined_names__icontains=maybe_club), type=ENTITY_CLUB
        )
        if not maybe_club or not query.exists():
            maybe_club = None

        # check if the second part is a club
        query = Entity.queryset_for_search(include_deleted=True).filter(
            Q(name__icontains=maybe_sponsor) | Q(joined_names__icontains=maybe_sponsor), type=ENTITY_CLUB
        )
        # HACK: edge case for KAIKU - IBERIA merge
        is_sponsor = maybe_sponsor in _KNOWN_SPONSORS and maybe_sponsor != 'IBERIA' and maybe_club != 'KAIKU'
        if not maybe_sponsor or not query.exists() or is_sponsor:
            maybe_sponsor = None

        if all_none(maybe_club, maybe_sponsor):
            return name

        name = " - ".join(i for i in [maybe_club, maybe_sponsor] if i is not None)
    return whitespaces_clean(name)
