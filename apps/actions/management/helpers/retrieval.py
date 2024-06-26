import logging
from collections.abc import Callable
from datetime import datetime

from apps.actions.management.helpers.input import input_club, input_edition
from apps.entities.models import Entity, League
from apps.entities.services import EntityService, LeagueService
from apps.races.models import Flag, Race, Trophy
from pyutils.strings import remove_parenthesis
from rscraping.data.checks import is_memorial, is_play_off
from rscraping.data.constants import ENTITY_CLUB
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


def retrieve_competition[T: (Trophy, Flag)](
    _model: type[T],
    race: RSRace,
    db_race: Race | None,
    closest_by_name: Callable[[str], T | None],
    infer_edition: Callable[[T, str, str, int], int | None],
) -> tuple[T | None, int | None]:
    value, edition = None, None
    model_name = _model.__name__.lower()

    # 1. try to load from local race
    if db_race and getattr(db_race, model_name):
        logger.debug(f"found {_model.__name__.lower()} in database race")
        return getattr(db_race, model_name), getattr(db_race, f"{model_name}_edition")

    # 2. try to found matching value
    for name, ed in race.normalized_names:
        if len(race.normalized_names) > 1 and is_memorial(name):
            continue

        if not value:
            value, edition = closest_by_name(name), ed

    # 2.1. try to infer edition
    if value and not edition:
        logger.debug(f"found closest {_model.__name__.lower()}={value} by name")
        logger.debug(f"infering edition for {value=}")
        edition = infer_edition(
            value,
            str(race.gender),
            str(race.category),
            datetime.strptime(race.date, "%d/%m/%Y").date().year,
        )
        edition = input_edition(model=value, league=race.league) if not edition else edition

    # 2.2. return value and edition
    if value and edition:
        logger.info(f"inferred edition for {_model.__name__.lower()}")
        return value, int(edition)

    logger.info("unable to infer edition")
    return None, None


def retrieve_league(race: RSRace, db_race: Race | None) -> League | None:
    if db_race:
        return db_race.league

    if race.league and not is_play_off(remove_parenthesis(race.name)):
        return LeagueService.get_by_name(race.league)

    return None


def retrieve_entity(
    name: str,
    clean: Callable[[str], str] | None = None,
    entity_type: str | None = ENTITY_CLUB,
) -> Entity | None:
    try:
        return EntityService.get_closest_by_name_type(name, entity_type=entity_type, include_deleted=True)
    except Entity.MultipleObjectsReturned:
        raise AssertionError(f"multiple entities found for {name=}")
    except Entity.DoesNotExist:
        pass

    if clean:
        return retrieve_entity(clean(name))

    return input_club(name)
