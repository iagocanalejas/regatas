import logging
import operator
from functools import reduce

from django.db.models import Q

from apps.races.models import Flag, Trophy
from pyutils.strings import closest_result, expand_lemmas, normalize_synonyms, whitespaces_clean
from rscraping import SYNONYMS, lemmatize

logger = logging.getLogger(__name__)


TOKEN_EXPANSIONS = [
    ["trofeo", "bandera", "regata"],
    ["trainera", None],
    ["femenino", None],
]


def get_closest_by_name[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    :return: closest found Flag|Trophy in the database or raise DoesNotExist
    """
    trophy = _get_closest_by_name_with_tokens(_model, name.upper())
    return trophy or _get_closest_by_name(_model, name.upper())


def get_closest_by_name_or_none[T: (Trophy, Flag)](_model: type[T], name: str) -> T | None:
    """
    :return: closest found Flag|Trophy in the database or None
    """
    try:
        get_closest_by_name(_model, name)
    except _model.DoesNotExist:
        return None


def get_closest_by_name_or_create[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    :return: closest found Flag|Trophy in the database or a newly created one
    """
    try:
        item = get_closest_by_name(_model, name)
    except _model.DoesNotExist:
        item = _model(name=name.upper())
        item.save()

        logger.info(f"created:: {item}")
    return item


def _get_closest_by_name_with_tokens[T: (Trophy, Flag)](_model: type[T], name: str) -> T | None:
    """
    Use lemma expansion to find a Flag or Trophy by filtering using tokens.

    The `_get_closest_by_name_with_tokens` function takes a model type `_model` and a name as input and uses lemma
    expansion to find the closest matching object of type `T` (Flag or Trophy) by filtering using tokens.

    Parameters:
        _model (Type[T]): The model type representing either `Flag` or `Trophy`.
        name (str): The name to search for the closest match.

    Returns:
        Optional[T]: The closest matching object of type `T` (Flag or Trophy), or None if no match is found.

    Note:
        This function utilizes lemma expansion to handle variations of the input name, synonyms, and whitespace.
        It filters objects based on matching tokens in their names.
    """

    # try search by tokens
    name = whitespaces_clean(normalize_synonyms(name, SYNONYMS))
    tokens = expand_lemmas(list(lemmatize(name)), TOKEN_EXPANSIONS)
    trophies = _model.objects.filter(reduce(operator.or_, [Q(tokens__contains=list(n)) for n in tokens]))

    count = trophies.count()
    if not count:
        return
    if count == 1:
        return trophies.first()

    # try to improve if we have many results
    trophies = trophies.filter(reduce(operator.or_, [Q(tokens__contained_by=list(n)) for n in tokens]))
    if trophies.count() == 1:
        return trophies.first()


def _get_closest_by_name[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    Retrieve the closest matching Flag or Trophy from the database.

    The `_get_closest_by_name` function takes a model type `_model` and a name as input and returns the closest
    matching object of type `T` (Flag or Trophy) from the database.

    Parameters:
        _model (Type[T]): The model type representing either `Flag` or `Trophy`.
        name (str): The name to search for the closest match.

    Returns:
        T: The closest matching object of type `T` (Flag or Trophy) from the database.

    Raises:
        T.DoesNotExist: If no close match is found in the database or the match's similarity threshold is below 0.85.

    Note:
        This function internally uses a normalization process to handle synonyms, whitespace, and case-insensitivity
        in the name search.
    """

    def normalize(name: str) -> str:
        return whitespaces_clean(normalize_synonyms(name, SYNONYMS))

    # retrieve the matches and un-flag them
    trophies = _model.objects.filter(reduce(operator.and_, [Q(name__icontains=n) for n in name.split()]))
    matches = [(i, normalize(i)) for i in list(trophies.values_list("name", flat=True))]

    closest, threshold = closest_result(normalize(name), [m for _, m in matches]) if matches else (None, 0)
    if not closest or threshold < 0.85:
        raise _model.DoesNotExist(f"{_model.__name__} with {name=}")

    # retrieve the un-flag name
    closest = [k for k, m in matches if m == closest][0]
    return _model.objects.get(name=closest)
