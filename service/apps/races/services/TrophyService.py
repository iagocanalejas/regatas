from apps.races.models import Trophy
from apps.races.services import _common


def get_closest_by_name(name: str) -> Trophy:
    """
    :return: closest found trophy in the database or raise Trophy.DoesNotExist
    """
    return _common.get_closest_by_name(Trophy, name)


def get_closest_by_name_or_none(name: str) -> Trophy | None:
    """
    :return: closest found trophy in the database or None
    """
    return _common.get_closest_by_name_or_none(Trophy, name)


def get_closest_by_name_or_create(name: str) -> Trophy:
    """
    :return: closest found trophy in the database or a newly created one
    """
    return _common.get_closest_by_name_or_create(Trophy, name)
