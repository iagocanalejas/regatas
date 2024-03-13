import logging

from django.db.models import QuerySet

from apps.races.models import Flag, Race, Trophy

logger = logging.getLogger(__name__)


def check_continuous_editions(model: type[Trophy | Flag] | None, **_):
    if not model:
        check_continuous_editions(Trophy)
        check_continuous_editions(Flag)
        return

    model_name = model.__name__.lower()
    logger.debug(f"searching throught {model_name}")
    for item in model.objects.all():
        races = Race.objects.filter(**{model_name: item}).order_by("league", f"{model_name}_edition", "day")
        if not _are_elements_continuous(races, model_name=model_name):
            logger.info(f"Missing edition in {model.__name__} {item.pk} - {item}")


def _are_elements_continuous(races: QuerySet[Race], model_name: str) -> bool:
    previous_race = None
    for race in races:
        if previous_race:
            edition = getattr(race, f"{model_name}_edition")
            previous_edition = getattr(previous_race, f"{model_name}_edition")

            if (
                previous_race.league_id == race.league_id  # pyright: ignore
                and edition - previous_edition != 1
                and (edition - previous_edition == 0 and race.day - previous_race.day != 1)
            ):
                return False

        previous_race = race
    return True
