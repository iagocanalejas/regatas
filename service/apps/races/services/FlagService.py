from typing import List

from apps.races.models import Flag
from apps.races.services import _common


def get() -> List[Flag]:
    """
    :return: all the flags
    """
    return Flag.objects.all()


def get_closest_by_name(name: str) -> Flag:
    """
    :return: closest found trophy in the database
    """
    return _common.get_closest_by_name(Flag, name)


def get_closest_by_name_or_create(name: str) -> Flag:
    """
    :return: closest found flag in the database or a newly created one
    """
    return _common.get_closest_by_name_or_create(Flag, name)
