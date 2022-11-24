from typing import List

from apps.races.models import Trophy
from apps.races.services import _common


def get() -> List[Trophy]:
    """
    :return: all the trophies
    """
    return Trophy.objects.all()


def get_closest_by_name(name: str) -> Trophy:
    """
    :return: closest found trophy in the database
    """
    return _common.get_closest_by_name(Trophy, name)


def get_closest_by_name_or_create(name: str) -> Trophy:
    """
    :return: closest found trophy in the database or a newly created one
    """
    return _common.get_closest_by_name_or_create(Trophy, name)
