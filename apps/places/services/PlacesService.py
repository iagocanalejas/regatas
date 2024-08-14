from django.core.exceptions import ObjectDoesNotExist

from apps.places.models import Place


def get_closest_by_name_or_none(name: str) -> Place | None:
    try:
        return get_closest_by_name(name)
    except Place.DoesNotExist:
        return None


def get_closest_by_name(name: str) -> Place | None:
    """
    :return: closest found place in the database
    """
    if not name:
        raise ValueError(f"invalid {name=}")

    try:
        return Place.searchable_objects.closest_by_name(name)
    except ObjectDoesNotExist:
        raise Place.DoesNotExist
