import logging
import time
from datetime import date, datetime

from django.core.management import BaseCommand
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.participants import preload_participants, save_participants_from_scraped_data
from apps.actions.management.helpers.races import save_race_from_scraped_data
from apps.races.services import MetadataService
from rscraping.clients import Client
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Datasource, Race

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Command class for importing data from a web datasource.

    This class provides functionality to import race data from a web datasource.
    The datasource can be specified as the first positional argument. The supported
    datasources are specified in the 'Datasource' enum.

    The command supports two ways of importing data:
    1. Importing data for a specific year.
    2. Importing data for all available years up to the current date.

    Usage:
    ------
    python manage.py scraperaces datasource year [--female] [--all]

    Arguments:
        datasource (str): The name of the web datasource to import data from. Supported
                          datasources are specified in the 'Datasource' enum.
        year (int): The year for which race data should be imported. This argument is required if
                    the '--all' option is not specified.

    Options:
        --female: (Optional) If specified, only import data for female races. If not specified,
                  both male and female races will be imported.
        --all: (Optional) If specified, import data for all available years up to the current date.
               If not specified, data for a specific 'year' should be provided.

    Note:
    -----
    - The command should be executed with appropriate arguments to import data from the desired web datasource.
    - The '--all' option allows importing data for all available years.
    - After importing, the parsed 'Race' and 'Participant' objects are iteratively saved to the database.
    - Avoid running this command frequently to avoid excessive web requests and database operations.
    """

    def add_arguments(self, parser):
        parser.add_argument("datasource", type=str, help="")
        parser.add_argument("year", default=None, type=int, help="")
        parser.add_argument("--female", action="store_true", default=False)
        parser.add_argument("--merge", action="store_true", default=False)
        parser.add_argument("--all", action="store_true", default=False)

    def handle(self, *_, **options):
        year, datasource, is_female, do_all, allow_merges = (
            options["year"],
            options["datasource"],
            options["female"],
            options["all"],
            options["merge"],
        )
        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")
        if not year and not do_all:
            raise ValueError("missing param 'year' | 'all'")

        if Datasource(datasource) == Datasource.LGT:
            is_female = None

        client: Client = Client(source=Datasource(datasource), is_female=is_female)  # type: ignore

        if do_all:
            year = client.FEMALE_START if is_female else client.MALE_START
            today = date.today()
            while year <= today.year:
                self._handle_year(client, year, Datasource(datasource), allow_merges=allow_merges, is_female=is_female)
                year += 1
                time.sleep(5)
        else:
            self._handle_year(client, year, Datasource(datasource), allow_merges=allow_merges, is_female=is_female)

    def _handle_year(
        self,
        client: Client,
        year: int,
        datasource: Datasource,
        allow_merges: bool,
        is_female: bool | None = None,
    ):
        for race_id in client.get_race_ids_by_year(year=year):
            if MetadataService.exists(race_id, datasource, gender=GENDER_FEMALE if is_female else None):
                continue
            time.sleep(1)

            try:
                race = client.get_race_by_id(race_id, is_female=is_female)
                if not race:
                    continue
            except ValueError as e:
                logger.error(e)
                continue

            logger.info(f"found race={race.name} for {race_id=}")

            is_after_today = datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()
            if is_after_today:
                break

            self._process_race(race, datasource=datasource, allow_merges=allow_merges)

    @staticmethod
    def _process_race(race: Race, datasource: Datasource, allow_merges: bool):
        participants = race.participants

        clubs = preload_participants(participants)
        try:
            new_race = save_race_from_scraped_data(race, datasource=datasource, allow_merges=allow_merges)
            save_participants_from_scraped_data(
                new_race,
                participants,
                preloaded_clubs=clubs,
                allow_merges=allow_merges,
            )
        except StopProcessing:
            logger.error(f"unable to save data for {race.race_id}::{race.name}")
