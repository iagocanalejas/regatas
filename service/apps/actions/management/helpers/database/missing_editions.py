import logging

from django.db.models import QuerySet

from apps.races.models import Flag, Race, Trophy

logger = logging.getLogger(__name__)


def missing_editions(model: str = "all", **_):
    if model == "all" or model in ["trophy", "trophies"]:
        _missing_trophy_editions()
    if model == "all" or model in ["flag", "flags"]:
        _missing_flag_editions()


def _missing_trophy_editions():
    def are_elements_continuous(races: QuerySet[Race]) -> bool:
        previous_race = None
        for race in races:
            if previous_race:
                next_trophy, trophy = race.trophy_edition, previous_race.trophy_edition
                assert next_trophy is not None and trophy is not None

                if (
                    previous_race.league_id == race.league_id  # pyright: ignore
                    and next_trophy - trophy != 1
                    and (next_trophy - trophy == 0 and race.day - previous_race.day != 1)
                ):
                    return False

            previous_race = race
        return True

    logger.debug("searching throught trophies")
    for trophy in Trophy.objects.all():
        races = Race.objects.filter(trophy=trophy).order_by("league", "trophy_edition", "day")
        if not are_elements_continuous(races):
            logger.info(f"Missing edition in Trophy {trophy.pk} - {trophy}")


def _missing_flag_editions():
    def are_elements_continuous(races: QuerySet[Race]) -> bool:
        previous_race = None
        for race in races:
            if previous_race:
                next_flag, flag = race.flag_edition, previous_race.flag_edition
                assert next_flag is not None and flag is not None

                if (
                    previous_race.league_id == race.league_id  # pyright: ignore
                    and next_flag - flag != 1
                    and (next_flag - flag == 0 and race.day - previous_race.day != 1)
                ):
                    return False

            previous_race = race
        return True

    logger.debug("searching throught flags")
    for flag in Flag.objects.all():
        races = Race.objects.filter(flag=flag).order_by("league", "flag_edition", "day")
        if not are_elements_continuous(races):
            logger.info(f"Missing edition in Flag {flag.pk} - {flag}")
