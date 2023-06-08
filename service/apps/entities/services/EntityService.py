import operator
from functools import reduce
from typing import Optional, List

from django.db.models import Q
from django.shortcuts import get_object_or_404
from unidecode import unidecode

from ai_django.ai_core.utils.lists import flatten
from ai_django.ai_core.utils.strings import closest_result, remove_conjunctions, remove_symbols, levenshtein_distance
from apps.entities.models import Entity
from utils.choices import ENTITY_CLUB, ENTITY_TYPES


def get(related: List[str] = None) -> List[Entity]:
    """
    :return: all the entities
    """
    entities = Entity.objects.all()
    return entities.select_related(*related) if related else entities


def get_clubs(related: List[str] = None) -> List[Entity]:
    """
    :return: all the CLUB entities
    """
    entities = Entity.objects.filter(type=ENTITY_CLUB)
    return entities.select_related(*related) if related else entities


def get_club_by_id(club_id: int, related: List[str] = None) -> List[Entity]:
    """
    :return: a CLUB entity
    """
    queryset = Entity.objects.filter(type=ENTITY_CLUB)
    queryset = queryset.select_related(*related) if related else queryset
    return get_object_or_404(queryset, pk=club_id)


def get_closest_club_by_name(name: str) -> Entity:
    """
    :return: closest found club in the database
    """
    return get_closest_by_name_type(name, entity_type=ENTITY_CLUB)


def get_closest_by_name_type(name: str, entity_type: Optional[str] = None) -> Entity:
    """
    :return: closest found @entity_type in the database
    """
    if entity_type and entity_type not in ENTITY_TYPES:
        raise ValueError(f'{entity_type=} should be one of {ENTITY_TYPES=}')

    if not name:
        raise ValueError(f'invalid {name=}')

    name = name.upper()
    parts = unidecode(remove_conjunctions(remove_symbols(name))).split()

    q = Entity.queryset_for_search().filter(type=entity_type) if entity_type else Entity.queryset_for_search()
    clubs = q.filter(reduce(operator.or_, [Q(name__unaccent__icontains=n) | Q(joined_names__unaccent__icontains=n) for n in parts]))

    matches = list(flatten(list(clubs.values_list('name', 'known_names'))))
    closest, closest_distance = closest_result(name, matches) if matches else (None, 0)

    if closest and closest_distance > .4:  # bigger is better
        if closest_distance == 1.0:
            return Entity.objects.get(Q(name=closest) | Q(known_names__contains=[closest]))

        avg_length = (len(closest) + len(name)) / 2
        normalized_levenshtein = levenshtein_distance(name, closest) / avg_length
        if normalized_levenshtein < .4:  # smaller is better
            return Entity.objects.get(Q(name=closest) | Q(known_names__contains=[closest]))

    raise Entity.DoesNotExist
