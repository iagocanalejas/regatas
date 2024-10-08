import logging
import operator
from functools import reduce

from django.db.models import Q

from apps.races.models import Flag, Race, Trophy
from pyutils.strings import (
    closest_result,
    expand_lemmas,
    normalize_synonyms,
    remove_parenthesis,
    unaccent,
    whitespaces_clean,
)
from rscraping.data.checks import is_memorial
from rscraping.data.constants import SYNONYMS
from rscraping.data.normalization import lemmatize

logger = logging.getLogger(__name__)


TOKEN_EXPANSIONS = [
    ["trofeo", "bandera", "regata"],
    ["trainera", None],
    ["femenino", None],
    ["masculino", None],
    ["ayuntamiento", None],
]


def get_or_none[T: (Trophy, Flag)](_model: type[T], id: int) -> T | None:
    """
    Returns: Flag|Trophy in the database or None
    """
    try:
        return _model.objects.get(id=id)
    except _model.DoesNotExist:
        return None


def get_closest_by_name[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    Returns: closest found Flag|Trophy in the database or raise DoesNotExist
    """
    item = _get_closest_by_name_with_tokens(_model, name.upper())
    return item if item else _get_closest_by_name_with_threshold(_model, name.upper())


def get_closest_by_name_or_none[T: (Trophy, Flag)](_model: type[T], name: str) -> T | None:
    """
    Returns: closest found Flag|Trophy in the database or None
    """
    try:
        return get_closest_by_name(_model, name)
    except _model.DoesNotExist:
        return None


def get_closest_by_name_or_create[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    Returns: closest found Flag|Trophy in the database or a newly created one
    """
    try:
        item = get_closest_by_name(_model, name)
    except _model.DoesNotExist:
        item = _model(name=name.upper())
        item.save()

        logger.info(f"created:: {item}")
    return item


def get_competition_or_none(names: list[str]) -> tuple[Trophy | None, Flag | None]:
    """
    Retrieve the closest Trophy and Flag competition based on a list of normalized names and their editions.

    Args:
        normalized_names (list[str]): A list of normalized names.

    Returns: tuple[Trophy, Flag]: A tuple containing the closest Trophy and Flag.
    """
    trophy, flag = None, None

    for name in names:
        if len(names) > 1 and is_memorial(name):
            continue

        if not trophy:
            trophy = get_closest_by_name_or_none(Trophy, name)
        if not flag:
            flag = get_closest_by_name_or_none(Flag, name)

    return trophy, flag


def infer_edition[T: (Trophy, Flag)](item: T, gender: str, category: str, year: int) -> int | None:
    """
    Returns: inferred edition for the Flag|Trophy given.
    """
    edition = _get_matching_edition(item, gender, category, year)
    if not edition:
        edition = _get_matching_edition(item, gender, category, year - 1)
        edition = edition + 1 if edition else None
    if not edition:
        edition = _get_matching_edition(item, gender, category, year + 1)
        edition = edition - 1 if edition else None
    return edition


def _get_closest_by_name_with_tokens[T: (Trophy, Flag)](_model: type[T], name: str) -> T | None:
    """
    Use lemma expansion to find a Flag or Trophy by filtering using tokens.

    The `_get_closest_by_name_with_tokens` function takes a model type `_model` and a name as input and uses lemma
    expansion to find the closest matching object of type `T` (Flag or Trophy) by filtering using tokens.

    Parameters:
        _model (Type[T]): The model type representing either `Flag` or `Trophy`.
        name (str): The name to search for the closest match.

    Returns: Optional[T]: The closest matching object of type `T` (Flag or Trophy), or None if no match is found.
    """

    # try search by tokens without expansion
    name = remove_parenthesis(name, preserve_content=True)
    name = whitespaces_clean(normalize_synonyms(name, SYNONYMS))
    tokens = [lemmatize(name)]
    unaccented_tokens = [[unaccent(name) for name in sublist] for sublist in tokens]

    items = _model.objects.filter(reduce(operator.or_, [Q(tokens__contains=sublist) for sublist in unaccented_tokens]))
    if items.count() == 1:
        return items.first()

    # try search by tokens with expansion
    tokens = expand_lemmas(lemmatize(name), TOKEN_EXPANSIONS)
    unaccented_tokens = [[unaccent(name) for name in sublist] for sublist in tokens]

    items = _model.objects.filter(reduce(operator.or_, [Q(tokens__contains=sublist) for sublist in unaccented_tokens]))

    count = items.count()
    if not count:
        return None
    if count == 1:
        return items.first()

    # try to improve search with 'ayuntamiento' lenma
    improved_items = items.filter(tokens__contains=["ayuntamiento"])
    if improved_items.count() == 1:
        return improved_items.first()

    # try to improve if we have many results
    improved_items = items.filter(reduce(operator.or_, [Q(tokens__contained_by=list(n)) for n in tokens]))
    if improved_items.count() == 1:
        return improved_items.first()


def _get_closest_by_name_with_threshold[T: (Trophy, Flag)](_model: type[T], name: str) -> T:
    """
    Retrieve the closest matching Flag or Trophy from the database.

    The `_get_closest_by_name` function takes a model type `_model` and a name as input and returns the closest
    matching object of type `T` (Flag or Trophy) from the database.

    Parameters:
        _model (Type[T]): The model type representing either `Flag` or `Trophy`.
        name (str): The name to search for the closest match.

    Returns: T: The closest matching object of type `T` (Flag or Trophy) from the database.
    """

    def normalize(name: str) -> str:
        return whitespaces_clean(normalize_synonyms(name, SYNONYMS))

    # retrieve the matches and un-flag them
    items = _model.objects.filter(reduce(operator.and_, [Q(name__icontains=n) for n in name.split()]))
    matches = [(i, normalize(i)) for i in list(items.values_list("name", flat=True))]

    closest, threshold = closest_result(normalize(name), [m for _, m in matches]) if matches else (None, 0)
    if not closest or threshold < 0.85:
        raise _model.DoesNotExist(f"{_model.__name__} with {name=}")

    # retrieve the un-flag name
    closest = [k for k, m in matches if m == closest][0]
    return _model.objects.get(name=closest)


def _get_matching_edition[T: (Trophy, Flag)](item: T, gender: str, category: str, year: int) -> int | None:
    """
    Tries to retrieve the edition for a Trophy or Flag model instance.

    Args:
        item (T): The Trophy or Flag instance for which the edition is sought.
        gender (str): The gender associated with the race.
        year (int): The year for which the edition is to be retrieved.

    Returns:
        int | None: The edition of the Trophy or Flag model for the given year and gender.
        Returns None if no match is found.
    """
    model_name = type(item).__name__.lower()
    matches = Race.objects.filter(
        Q(**{f"{model_name}__isnull": True}) | Q(**{f"{model_name}": item}),
        gender=gender,
        category=category,
        date__year=year,
        day=1,
    )
    if matches.count() == 1:
        return getattr(matches.get(), f"{model_name}_edition")
    if matches.count() > 1:
        editions = list(matches.values_list(f"{model_name}_edition", flat=True))
        if all(e == editions[0] for e in editions):
            return editions[0]
    return None
