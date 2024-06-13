from apps.races.models import Trophy
from apps.races.services import CompetitionService


def get_closest_by_name(name: str) -> Trophy:
    """
    Returns: closest found trophy in the database or raise Trophy.DoesNotExist
    """
    return CompetitionService.get_closest_by_name(Trophy, name)


def get_closest_by_name_or_none(name: str) -> Trophy | None:
    """
    Returns: closest found trophy in the database or None
    """
    return CompetitionService.get_closest_by_name_or_none(Trophy, name)


def get_closest_by_name_or_create(name: str) -> Trophy:
    """
    Returns: closest found trophy in the database or a newly created one
    """
    return CompetitionService.get_closest_by_name_or_create(Trophy, name)


def infer_trophy_edition(trophy: Trophy, gender: str, category: str, year: int) -> int | None:
    """
    Returns: inferred edition for the given trophy.
    """
    return CompetitionService.infer_edition(trophy, gender, category, year)
