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
from rscraping.clients import Client, ClientProtocol
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN, GENDER_FEMALE
from rscraping.data.models import Datasource, Participant, Race
from rscraping.parsers.html import MultiDayRaceException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data, in bulk, from a web datasource or folder.

    Usage:
    python manage.py your_command datasource_or_folder [year] [--female] [--ignore ID [ID ...]] [-o OUTPUT]

    Arguments:
        datasource_or_folder    The name of the web datasource or local folder or path to a folder to import data from.
        year (optional)         The year for which races data should be imported.

    Options:
        -f, --female                If specified, import data for female races.
        -c, --category              If specified, import data for the given category (ABSOLUT | VETERAN | SCHOOL).
        --ignore ID [ID ...]        List of race IDs to ignore during import.
        -o, --output OUTPUT         Output path to save the scrapped data.
    """

    _ignored_races: list[str] = []
    _processed_files: list[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            "datasource_or_folder", type=str, help="The name of the web datasource or local folder to import data from."
        )
        parser.add_argument(
            "year", nargs="?", type=int, default=None, help="The year for which race data should be imported."
        )
        parser.add_argument(
            "-f", "--female", action="store_true", default=False, help="If specified, import data for female races."
        )
        parser.add_argument(
            "-c", "--category", type=str, default=None, help="If specified, import data for the given category."
        )
        parser.add_argument("--ignore", type=str, nargs="*", default=[], help="List of ignored IDs.")
        parser.add_argument("-o", "--output", type=str, default=None, help="Output path to save the scrapped data.")

    @staticmethod
    def _validate_arguments(
        maybe_datasource: str, year: int | None, category: str | None
    ) -> tuple[Datasource, int, str | None]:
        if not year:
            raise ValueError("required value for 'year'")

        if not maybe_datasource or not Datasource.has_value(maybe_datasource):
            raise ValueError(f"invalid datasource={maybe_datasource}")
        if category and maybe_datasource != Datasource.TRAINERAS:
            raise ValueError(f"category filtering is not suported in datasource={maybe_datasource}")
        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")
        return Datasource(maybe_datasource), year, category.upper() if category else None

    def handle(self, *_, **options):
        logger.info(f"{options}")

        year, datasource_or_folder, is_female, category, self._ignored_races, output_path = (
            options["year"],
            options["datasource_or_folder"],
            options["female"],
            options["category"],
            options["ignore"],
            options["output"],
        )

        # handle folder
        if os.path.isdir(datasource_or_folder):
            try:
                self._process_folder(datasource_or_folder)
            finally:
                logging.info(f"procesed files: {" ".join(self._processed_files)}")
                logging.info(f"ignored races: {" ".join(self._ignored_races)}")
            return

        datasource, year, category = self._validate_arguments(datasource_or_folder, year, category)
        client: Client = Client(source=datasource)  # type: ignore

        # handle traineras.es special case
        if datasource == Datasource.TRAINERAS:
            try:
                self._process_traineras_year(client, year, is_female, category, output_path)
            finally:
                logging.info(f"ignored races: {" ".join(self._ignored_races)}")
            return

        try:
            self._process_year(client, year, is_female, output_path)
        finally:
            logging.info(f"ignored races: {" ".join(self._ignored_races)}")

    def _process_folder(self, path: str):
        for file_name in os.listdir(path):
            file = os.path.join(path, file_name)
            if os.path.isfile(file):
                logger.info(f"opening {file=}")
                race = load_race_from_file(file)
                self._process_race(race, Datasource(race.datasource), None)
                self._processed_files.append(file_name)
                os.remove(file)

    def _process_year(self, client: ClientProtocol, year: int, is_female: bool, output_path: str | None):
        def is_race_after_today(race: Race) -> bool:
            return datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()

        for race_id in client.get_race_ids_by_year(year=year, is_female=is_female):
            time.sleep(1)

            gender = GENDER_FEMALE if is_female else None
            if race_id in self._ignored_races or MetadataService.exists(race_id, client.DATASOURCE, gender=gender):
                continue

            try:
                race = client.get_race_by_id(race_id, is_female=is_female)
            except MultiDayRaceException as e:
                race_1 = client.get_race_by_id(race_id, is_female=is_female, day=1)
                race_2 = client.get_race_by_id(race_id, is_female=is_female, day=2)
                if not race_1 or not race_2:
                    raise e
                if is_race_after_today(race_1) or is_race_after_today(race_2):
                    break
                self._process_race(race_1, datasource=client.DATASOURCE, output_path=output_path)
                self._process_race(race_2, datasource=client.DATASOURCE, output_path=output_path)
                continue
            except ValueError as e:
                logger.error(e)
                continue

            if not race:
                continue

            if is_race_after_today(race):
                break

            logger.info(f"found race={race.name} for {race_id=}")
            self._process_race(race, datasource=client.DATASOURCE, output_path=output_path)

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

    def _process_traineras_year(
        self, client: ClientProtocol, year: int, is_female: bool, category: str | None, output_path: str | None
    ):
        current_processing: str | None = None
        race_ids = []
        for race in client.get_race_names_by_year(year, is_female=is_female, category=category):
            if race.name != current_processing:
                if len(race_ids) > 0:
                    self._process_traineras_race(client, race_ids, output_path)
                    time.sleep(2)
                current_processing = race.name
                race_ids = [race.race_id]
                continue
            race_ids.append(race.race_id)

    def _process_traineras_race(self, client: ClientProtocol, ids: list[str], output_path: str | None):
        race: Race | None = None
        participants: list[Participant] = []

        db_races = [MetadataService.get_race_or_none(ref, datasource=Datasource.TRAINERAS) for ref in ids]
        db_race = next(r for r in db_races if r is not None)

        logger.info(f"merging {len(ids)} races")
        for race_id in ids:
            if race_id in self._ignored_races:
                continue

            local_race = client.get_race_by_id(race_id, is_female=False)  # is_female is ignored in TrainerasClient
            time.sleep(1)

            if not local_race:
                continue

            participants += local_race.participants
            local_race.participants = []

            if not race:
                race = local_race

            # TODO: how to merge races
            print(race.__dict__.items() ^ local_race.__dict__.items())

        if not race:
            logger.error(f"unable to save data for {ids=}")
            return

        if output_path and os.path.isdir(output_path):
            save_race_to_file(race, output_path)
            return

        clubs = preload_participants(participants)
        try:
            new_race = save_race_from_scraped_data(race, datasource=Datasource.TRAINERAS) if not db_race else db_race
            save_participants_from_scraped_data(new_race, participants, preloaded_clubs=clubs)
        except StopProcessing as e:
            logger.error(e)
            logger.error(f"unable to save data for {race.race_id}::{race.name}")
            self._ignored_races.append(race.race_id)
