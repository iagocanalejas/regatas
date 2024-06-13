from apps.races.models import Flag
from apps.races.services import CompetitionService


def get_closest_by_name(name: str) -> Flag:
    """
    Returns: closest found flag in the database or raise Flag.DoesNotExist
    """
    return CompetitionService.get_closest_by_name(Flag, name)


def get_closest_by_name_or_none(name: str) -> Flag | None:
    """
    Returns: closest found flag in the database or None
    """
    return CompetitionService.get_closest_by_name_or_none(Flag, name)


def get_closest_by_name_or_create(name: str) -> Flag:
    """
    Returns: closest found flag in the database or a newly created one
    """
    return CompetitionService.get_closest_by_name_or_create(Flag, name)


def infer_flag_edition(flag: Flag, gender: str, category: str, year: int) -> int | None:
    """
    Returns: inferred edition for the given flag.
    """
    return CompetitionService.infer_edition(flag, gender, category, year)
