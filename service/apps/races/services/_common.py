import logging
import operator
from functools import reduce
from typing import TypeVar, Type, Optional

from django.db.models import Q
from unidecode import unidecode

from ai_django.ai_core.utils.strings import remove_symbols, remove_conjunctions, closest_result, whitespaces_clean
from apps.races.models import Flag, Trophy
from utils.synonyms import normalize_synonyms, lemmatize, expand_lemmas

logger = logging.getLogger(__name__)

T = TypeVar("T", Trophy, Flag)


def get_closest_by_name(_model: Type[T], name: str) -> T:
    """
    :return: closest found Flag|Trophy in the database
    """
    name = name.upper()

    # try search by tokens
    trophy = _get_closest_by_name_with_tokens(_model, name)
    return trophy or _get_closest_by_name(_model, name)


def get_closest_by_name_or_create(_model: Type[T], name: str) -> T:
    """
    :return: closest found Flag|Trophy in the database or a newly created one
    """
    try:
        item = get_closest_by_name(_model, name)
    except _model.DoesNotExist:
        item = _model(name=name.upper())
        item.save()

        logger.info(f'created:: {item}')
    return item


def _get_closest_by_name_with_tokens(_model: Type[T], name: str) -> Optional[T]:
    """
    Use lemma expansion to find a Flag|Trophy filtering by the tokens
    """
    # try search by tokens
    tokens = expand_lemmas(lemmatize(name))
    trophies = _model.objects.filter(
        reduce(
            operator.or_,
            [Q(tokens__contains=list(n)) for n in tokens]
        )
    )

    count = trophies.count()
    if not count:
        return
    if count == 1:
        return trophies.first()

    # try to improve if we have many results
    trophies = trophies.filter(
        reduce(
            operator.or_,
            [Q(tokens__contained_by=list(n)) for n in tokens]
        )
    )
    if trophies.count() == 1:
        return trophies.first()


def _get_closest_by_name(_model: Type[T], name: str) -> T:
    """
    :return: closest found Flag|Trophy in the database
    """
    name = _normalize(name)
    parts = name.split()

    trophies = _model.objects.filter(
        reduce(
            operator.and_,
            [Q(name__unaccent__icontains=n) for n in parts]
        )
    )

    # retrieve the matches and un-flag them
    matches = [(i, _normalize(i)) for i in list(trophies.values_list('name', flat=True))]

    closest, threshold = closest_result(name, [m for _, m in matches]) if matches else (None, 0)
    if not closest or threshold < 0.85:
        raise _model.DoesNotExist

    # retrieve the un-flag name
    closest = [k for k, m in matches if m == closest][0]
    return _model.objects.get(name=closest)


def _normalize(name: str) -> str:
    name = normalize_synonyms(name)
    name = remove_symbols(unidecode(remove_conjunctions(name)))
    return whitespaces_clean(name)
