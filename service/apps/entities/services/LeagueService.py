from typing import List

from apps.entities.models import League
from rscraping.data.normalization.leagues import normalize_league_name


def get_with_parent() -> List[League]:
    """
    :return: all the leagues with parent
    """
    return League.objects.filter(parent__isnull=False)


def get_by_name(name: str) -> League:
    """
    :return: matching league in the database
    """
    name = normalize_league_name(name)

    return League.objects.get(name=name)
