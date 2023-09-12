import logging

from django.core.management import BaseCommand
from utils.choices import GENDER_FEMALE
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.helpers import (
    preload_participants,
    save_participants_from_scraped_data,
    save_race_from_scraped_data,
)
from apps.races.services import RaceService
from rscraping import Datasource, find_race

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Command class for finding and scraping a specific race from a web datasource.

    This class provides functionality to search for a specific race on a web datasource
    and scrape its data. The datasource can be specified as the first positional argument.
    The supported datasources are specified in the 'Datasource' enum.

    Usage:
    ------
    python manage.py findrace datasource race_id [--female]

    Arguments:
        datasource (str): The name of the web datasource from where to retrieve race data. Supported
                          datasources are specified in the 'Datasource' enum.
        race_id (str): The unique identifier of the race to find and scrape.

    Options:
        --female: (Optional) If specified, search and scrape data for female races. If not specified,
                  only male races will be searched. Applicable only when searching for a race.
        --day: (Optional) If specified, tries to find the day of the race in a multi-race page.
        --use-db: (Optional) If specified, uses the race found in the database instead of the one parsed.

    Note:
    -----
    - The command should be executed with appropriate arguments to find and scrape the desired race
      from the web datasource.
    - The 'race_id' argument is required to uniquely identify the race.
    - The '--female' option can be used to search and scrape only female races.
    - If the race is found, its data is scraped and saved to the database.
    - If the race already exists in the database, the command raises a 'StopProcessing' exception.
    """

    def add_arguments(self, parser):
        parser.add_argument("datasource", type=str, help="Datasource from where to retrieve.")
        parser.add_argument("race_id", type=str, help="Race to find.")
        parser.add_argument("--female", action="store_true", default=False)
        parser.add_argument("--day", type=int, help="Day of the race we want (used in multi-race pages).")
        parser.add_argument("--use-db", action="store_true", default=False)

    def handle(self, *_, **options):
        logger.info(f"{options}")

        race_id, datasource, is_female, day, use_db = (
            options["race_id"],
            options["datasource"],
            options["female"],
            options["day"],
            options["use_db"],
        )
        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")

        db_race = RaceService.get_by_datasource(
            race_id,
            Datasource(datasource),
            gender=GENDER_FEMALE if is_female else None,
            day=day,
        )
        if not use_db and db_race is not None:
            raise StopProcessing(f"race={race_id} already exists")

        web_race = find_race(race_id, datasource=Datasource(datasource), is_female=is_female, day=day)
        if not web_race:
            raise StopProcessing("no race found")

        participants = web_race.participants
        clubs = preload_participants(participants)

        new_race = db_race if use_db and db_race else save_race_from_scraped_data(web_race, Datasource(datasource))
        save_participants_from_scraped_data(new_race, participants, preloaded_clubs=clubs)
