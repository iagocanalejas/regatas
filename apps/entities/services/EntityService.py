import operator
from functools import reduce

from django.db.models import Q

from apps.entities.models import Entity
from apps.utils.choices import ENTITY_CLUB, ENTITY_TYPES
from pyutils.lists import flatten
from pyutils.strings import closest_result, levenshtein_distance, remove_conjunctions, remove_symbols


def get_entity_or_none(entity_id: int) -> Entity | None:
    try:
        return Entity.all_objects.get(id=entity_id)
    except Entity.DoesNotExist:
        return None


def get_closest_club_by_name(name: str, include_deleted: bool | None = None) -> Entity | None:
    """
    :return: closest found club in the database
    """
    try:
        return get_closest_by_name_type(name, entity_type=ENTITY_CLUB, include_deleted=include_deleted or False)
    except Entity.MultipleObjectsReturned:
        raise AssertionError(f"multiple clubs found for {name=}")
    except Entity.DoesNotExist:
        if include_deleted is None:
            return get_closest_club_by_name(name, include_deleted=True)
    return None


def get_closest_by_name_type(name: str, entity_type: str | None = None, include_deleted: bool = False) -> Entity:
    """
    :return: closest found @entity_type in the database
    """
    if entity_type and entity_type not in ENTITY_TYPES:
        raise ValueError(f"{entity_type=} should be one of {ENTITY_TYPES=}")

    if not name:
        raise ValueError(f"invalid {name=}")

    name = name.upper()
    name = name.rstrip(" B").rstrip(" C")
    parts = remove_conjunctions(remove_symbols(name)).split()

    q = Entity.queryset_for_search(include_deleted=include_deleted)
    q = q.filter(type=entity_type) if entity_type else q

    # quick route, just an exact match
    clubs = q.filter(Q(normalized_name__iexact=name) | Q(name__iexact=name) | Q(known_names__contains=[name]))
    if clubs.count() == 1:
        match = clubs.first()
        assert isinstance(match, Entity)
        return match

    # go for similarity
    clubs = q.filter(
        reduce(
            operator.or_,
            [Q(normalized_name__icontains=n) | Q(joined_names__icontains=n) for n in parts],
        )
    )

    if not clubs.exists():
        raise Entity.DoesNotExist

    matches = list(flatten(list(clubs.values_list("normalized_name", "known_names"))))
    closest, closest_distance = closest_result(name, matches) if matches else (None, 0)

    if closest and closest_distance > 0.4:  # bigger is better
        if closest_distance == 1.0:
            q = Entity.all_objects if include_deleted else Entity.objects
            return q.get(Q(normalized_name=closest) | Q(known_names__contains=[closest]))

        avg_length = (len(closest) + len(name)) / 2
        normalized_levenshtein = levenshtein_distance(name, closest) / avg_length
        if normalized_levenshtein < 0.4:  # smaller is better
            q = Entity.all_objects if include_deleted else Entity.objects
            return q.get(Q(normalized_name=closest) | Q(known_names__contains=[closest]))

    raise Entity.DoesNotExist
