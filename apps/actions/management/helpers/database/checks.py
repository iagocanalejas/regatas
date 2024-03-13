import logging

from apps.races.models import Flag, Race, Trophy
from rscraping.data.constants import GENDER_ALL, GENDER_FEMALE, GENDER_MALE

logger = logging.getLogger(__name__)


def check_values(model: type[Trophy | Flag] | None, value: str, **_):
    if not model:
        check_values(Trophy, value)
        check_values(Flag, value)
        return

    assert value in ["laps", "lanes"]

    model_name = model.__name__.lower()
    logger.debug(f"searching throught {model_name}")
    for gender in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL]:
        for item in model.objects.all():
            races = Race.objects.filter(gender=gender, **{model_name: item})
            if not races:
                continue

            if any(getattr(race, value) != getattr(races[0], value) for race in races):
                choices = set([getattr(race, value) for race in races])
                logger.info(f"found different {choices=} for {value} in {model_name} {item}")


def check_genders():
    query = """
        SELECT * FROM race r 
        WHERE (SELECT count(distinct gender) FROM participant p WHERE p.race_id = r.id) > 1 
            AND r.gender != 'ALL'
    """
    races = Race.objects.raw(query)
    for race in races:
        logger.info(f"found different genders for {race=}")
