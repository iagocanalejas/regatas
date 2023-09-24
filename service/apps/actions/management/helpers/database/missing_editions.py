import logging
from typing import List

from apps.races.models import Flag, Race, Trophy

logger = logging.getLogger(__name__)


def missing_editions():
    _missing_trophy_editions()
    _missing_flag_editions()


def _missing_trophy_editions():
    def are_elements_continuous(races: List[Race]) -> bool:
        for i in range(len(races) - 1):
            next_race, race = races[i + 1], races[i]
            next_trophy, trophy = next_race.trophy_edition, race.trophy_edition

            assert next_trophy is not None and trophy is not None

            if (
                next_race.league_id == race.league_id  # pyright: ignore
                and next_trophy - trophy != 1
                and (next_trophy - trophy == 0 and next_race.day - race.day != 1)
            ):
                return False
        return True

    logger.debug("searching throght trophies")
    for trophy in Trophy.objects.all():
        races = Race.objects.filter(trophy=trophy).order_by("league", "trophy_edition", "day")
        if not are_elements_continuous(list(races)):
            print(f"{trophy.pk} - {trophy}")


def _missing_flag_editions():
    def are_elements_continuous(races: List[Race]) -> bool:
        for i in range(len(races) - 1):
            next_race, race = races[i + 1], races[i]
            next_flag, flag = next_race.flag_edition, race.flag_edition

            assert next_flag is not None and flag is not None

            if (
                next_race.league_id == race.league_id  # pyright: ignore
                and next_flag - flag != 1
                and (next_flag - flag == 0 and next_race.day - race.day != 1)
            ):
                return False
        return True

    logger.debug("searching throght flags")
    for flag in Flag.objects.all():
        races = Race.objects.filter(flag=flag).order_by("league", "flag_edition", "day")
        if not are_elements_continuous(list(races)):
            print(f"{flag.pk} - {flag}")
