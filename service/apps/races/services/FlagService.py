from apps.races.models import Flag
from apps.races.services import _common


def get_closest_by_name(name: str) -> Flag:
    """
    :return: closest found trophy in the database or raise Flag.DoesNotExist
    """
    return _common.get_closest_by_name(Flag, name)


def get_closest_by_name_or_none(name: str) -> Flag | None:
    """
    :return: closest found flag in the database or None
    """
    return _common.get_closest_by_name_or_none(Flag, name)


def get_closest_by_name_or_create(name: str) -> Flag:
    """
    :return: closest found flag in the database or a newly created one
    """
    return _common.get_closest_by_name_or_create(Flag, name)
