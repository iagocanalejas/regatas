import logging
import time
from datetime import date, datetime
from typing import List, Optional

from django.core.management import BaseCommand
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.helpers import (
    preload_participants,
    save_participants_from_scraped_data,
    save_race_from_scraped_data,
)
from apps.races.services import RaceService
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
        parser.add_argument("--all", action="store_true", default=False)

    def handle(self, *_, **options):
        year, datasource, is_female, do_all = options["year"], options["datasource"], options["female"], options["all"]
        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")
        if not year and not do_all:
            raise ValueError("missing param 'year' | 'all'")

        if Datasource(datasource) == Datasource.LGT:
            is_female = None

        items: List[Race] = []
        client: Client = Client(source=Datasource(datasource), is_female=is_female)  # type: ignore

        if do_all:
            year = client.FEMALE_START if is_female else client.MALE_START
            today = date.today()
            while year <= today.year:
                items.extend(self._handle_year(client, year, Datasource(datasource), is_female=is_female))
                year += 1
                time.sleep(5)
        else:
            items.extend(self._handle_year(client, year, Datasource(datasource), is_female=is_female))

        for race in items:
            participants = race.participants

            clubs = preload_participants(participants)
            try:
                new_race = save_race_from_scraped_data(race, Datasource(datasource))
                save_participants_from_scraped_data(new_race, participants, preloaded_clubs=clubs)
            except StopProcessing:
                logger.error(f"unable to save data for {race.race_id}::{race.name}")
                continue

    @staticmethod
    def _handle_year(client: Client, year: int, datasource: Datasource, is_female: Optional[bool] = None) -> List[Race]:
        items: List[Race] = []

        race_ids = client.get_race_ids_by_year(year=year)
        race_ids = [
            r
            for r in race_ids
            if not RaceService.get_by_datasource(r, datasource, gender=GENDER_FEMALE if is_female else None)
        ]
        logger.info(f"found {len(race_ids)} races for {year=}")

        for race_id in race_ids:
            time.sleep(1)

            try:
                race = client.get_race_by_id(race_id, is_female=is_female)
            except ValueError as e:
                logger.error(e)
                continue
            if not race:
                continue
            logger.info(f"found race={race.name} for {race_id=}")

            is_after_today = race and datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()
            if is_after_today:
                break

            items.append(race)

        items = [i for i in items if i is not None]
        logger.info(f"parsed {len(items)} races for {year=}")
        return items
