#!/usr/bin/env python3

import logging
import os

from django.core.management import BaseCommand
from utils.choices import GENDER_FEMALE
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.participants import preload_participants, save_participants_from_scraped_data
from apps.actions.management.helpers.races import load_race_from_file, save_race_from_scraped_data, save_race_to_file
from apps.races.models import Race
from apps.races.services import MetadataService
from rscraping import Datasource, find_race
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource or file.

    Usage:
    ------
    python manage.py findrace datasource_or_file [race_id] [--female] [--day DAY] [--use-db]

    Arguments:
        datasource_or_file   Datasource or file from where to retrieve the race data.
        race_id (optional)   Race to find (required if the datasource_or_file is a file).

    Options:
        --day DAY            Day of the race (used in multi-race pages).
        --female             Specify if the race is female.
        -o, --output OUTPUT  Output path to save the scrapped data.
        --use-db             Use the database to retrieve race data.
    """

    def add_arguments(self, parser):
        parser.add_argument("datasource_or_file", type=str, help="Datasource or file from where to retrieve.")
        parser.add_argument("race_id", nargs="?", type=str, default=None, help="Race to find.")
        parser.add_argument("--day", type=int, help="Day of the race we want (used in multi-race pages).")
        parser.add_argument("--female", action="store_true", default=False, help="When to use female logic.")
        parser.add_argument("-o", "--output", type=str, default=None, help="Output path to save the scrapped data.")
        parser.add_argument("--use-db", action="store_true", default=False, help="When to use database data.")

    def handle(self, *_, **options):
        logger.info(f"{options}")

        race_id, datasource_or_file, is_female, day, use_db, output_path = (
            options["race_id"],
            options["datasource_or_file"],
            options["female"],
            options["day"],
            options["use_db"],
            options["output"],
        )

        race: RSRace | None = None
        if not os.path.isfile(datasource_or_file):
            datasource = datasource_or_file
            if not race_id:
                raise ValueError("required value for 'race_id'")
        else:
            race = self._load_race_from_file(datasource_or_file)
            race_id, datasource = race.race_id, race.datasource

        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")
        datasource = Datasource(datasource)

        db_race = self._retrieve_database_race(race_id, datasource, day, is_female, use_db)

        if not race:
            race = find_race(race_id, datasource=Datasource(datasource), is_female=is_female, day=day)

        if not race:
            raise StopProcessing("no race found")

        if output_path and os.path.isdir(output_path):
            save_race_to_file(race, output_path)
            return

        participants = race.participants
        clubs = preload_participants(participants)

        new_race = db_race if use_db and db_race else save_race_from_scraped_data(race, Datasource(datasource))
        save_participants_from_scraped_data(new_race, participants, preloaded_clubs=clubs)

    def _load_race_from_file(self, path: str) -> RSRace:
        race = load_race_from_file(path)
        if not race.race_id:
            raise ValueError("required value for 'race_id'")
        if not race.datasource:
            raise ValueError("required value for 'datasource'")
        logger.info("loaded race from file")
        return race

    def _retrieve_database_race(
        self,
        race_id: str,
        datasource: Datasource,
        day: int,
        is_female: bool,
        use_db: bool,
    ) -> Race | None:
        race = MetadataService.get_race_or_none(
            race_id,
            Datasource(datasource),
            gender=GENDER_FEMALE if is_female else None,
            day=day,
        )
        if not use_db and race is not None:
            raise StopProcessing(f"race={race_id} already in database")
        return race
