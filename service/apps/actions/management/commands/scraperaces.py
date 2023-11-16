#!/usr/bin/env python3

import logging
import os
import time
from datetime import date, datetime

from django.core.management import BaseCommand
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.participants import preload_participants, save_participants_from_scraped_data
from apps.actions.management.helpers.races import load_race_from_file, save_race_from_scraped_data, save_race_to_file
from apps.races.services import MetadataService
from rscraping.clients import Client
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Datasource, Race
from rscraping.parsers.html import MultiDayRaceException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data, in bulk, from a web datasource or folder.

    Usage:
    python manage.py your_command datasource_or_folder [year] [--female] [--ignore ID [ID ...]] [-o OUTPUT]

    Arguments:
        datasource_or_folder    The name of the web datasource or path to a folder to import data from.
        year (optional)         The year for which races data should be imported.

    Options:
        --female                If specified, import data for female races.
        --ignore ID [ID ...]    List of race IDs to ignore during import.
        -o, --output OUTPUT     Output path to save the scrapped data.
    """

    _ignored_races: list[str] = []
    _processed_files: list[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            "datasource_or_folder",
            type=str,
            help="The name of the web datasource to import data from.",
        )
        parser.add_argument(
            "year",
            nargs="?",
            type=int,
            default=None,
            help="The year for which race data should be imported.",
        )
        parser.add_argument(
            "--female",
            action="store_true",
            default=False,
            help="If specified, import data for female races.",
        )
        parser.add_argument("--ignore", type=str, nargs="*", default=[], help="List of ignored IDs.")
        parser.add_argument("-o", "--output", type=str, default=None, help="Output path to save the scrapped data.")

    def handle(self, *_, **options):
        logger.info(f"{options}")

        year, datasource_or_folder, is_female, self._ignored_races, output_path = (
            options["year"],
            options["datasource_or_folder"],
            options["female"],
            options["ignore"],
            options["output"],
        )

        if not os.path.isdir(datasource_or_folder):
            datasource = datasource_or_folder
            if not year:
                raise ValueError("required value for 'year'")
        else:
            try:
                self._handle_folder(datasource_or_folder)
            finally:
                logging.info(f"procesed files: {" ".join(self._processed_files)}")
                logging.info(f"ignored races: {" ".join(self._ignored_races)}")
            return

        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")

        datasource = Datasource(datasource)
        client: Client = Client(source=datasource)  # type: ignore

        try:
            self._handle_year(client, year, datasource, output_path, is_female=is_female)
        finally:
            logging.info(f"ignored races: {" ".join(self._ignored_races)}")

    def _handle_folder(self, path: str):
        for file_name in os.listdir(path):
            file = os.path.join(path, file_name)
            if os.path.isfile(file):
                logger.info(f"opening {file=}")
                race = load_race_from_file(file)
                self._process_race(race, Datasource(race.datasource), None)
                self._processed_files.append(file_name)

    def _handle_year(
        self,
        client: Client,
        year: int,
        datasource: Datasource,
        output_path: str | None,
        is_female: bool,
    ):
        def is_after_today(race: Race) -> bool:
            return datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()

        for race_id in client.get_race_ids_by_year(year=year, is_female=is_female):
            time.sleep(1)

            gender = GENDER_FEMALE if is_female else None
            if race_id in self._ignored_races or MetadataService.exists(race_id, datasource, gender=gender):
                continue

            try:
                race = client.get_race_by_id(race_id, is_female=is_female)
            except MultiDayRaceException as e:
                race_1 = client.get_race_by_id(race_id, is_female=is_female, day=1)
                race_2 = client.get_race_by_id(race_id, is_female=is_female, day=2)
                if not race_1 or not race_2:
                    raise e
                if is_after_today(race_1) or is_after_today(race_2):
                    break
                self._process_race(race_1, datasource=datasource, output_path=output_path)
                self._process_race(race_2, datasource=datasource, output_path=output_path)
                continue
            except ValueError as e:
                logger.error(e)
                continue

            if not race:
                continue

            if is_after_today(race):
                break

            logger.info(f"found race={race.name} for {race_id=}")
            self._process_race(race, datasource=datasource, output_path=output_path)

    def _process_race(self, race: Race, datasource: Datasource, output_path: str | None):
        if output_path and os.path.isdir(output_path):
            save_race_to_file(race, output_path)
            return

        participants = race.participants

        clubs = preload_participants(participants)
        try:
            new_race = save_race_from_scraped_data(race, datasource=datasource)
            save_participants_from_scraped_data(new_race, participants, preloaded_clubs=clubs)
        except StopProcessing as e:
            logger.error(e)
            logger.error(f"unable to save data for {race.race_id}::{race.name}")
            self._ignored_races.append(race.race_id)
