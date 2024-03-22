#!/usr/bin/env python3

import json
import logging
import os

from django.core.management import BaseCommand

from apps.actions.management.helpers.input import input_race
from apps.actions.management.ingestor import build_ingestor
from rscraping.clients import TabularClientConfig
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file and spreadsheet.

    Usage:
    python manage.py scraperaces input_source [year] \
        [-f, --female] \
        [-c, --category CATEGORY] \
        [--sheet-id SHEET_ID] \
        [--sheet-name SHEET_NAME] \
        [--file-path FILE_PATH] \
        [-i, --ignore ID [ID ...]] \
        [-o, --output OUTPUT]

    Arguments:
        input_source:
            The name of the Datasource or path to import data from.

        year:
            The year for which race data should be imported.
            NOTE: This argument is mandatory for Datasource and not supported for local files.

    Options:
        -f, --female:
            Import data for female races.

        -c, --category:
            Import data for the given category (ABSOLUT | VETERAN | SCHOOL).
            NOTE: This option is only supported for the TRAINERAS datasource.

        --sheet-id:
            Google sheet ID used for TABULAR datasource.

        --sheet-name:
            Google sheet name used for TABULAR datasource.

        --file-path:
            Sheet file path used for TABULAR datasource.

        -i, --ignore:
            List of race IDs to ignore during ingestion.

        -o, --output:
            Outputs the race data to the given folder path in JSON format.
    """

    _ignored_races: list[str] = []

    def add_arguments(self, parser):
        parser.add_argument("input_source", type=str, help="The name of the Datasource or path to import data from")
        parser.add_argument(
            "year",
            nargs="?",
            type=int,
            default=None,
            help="The year for which race data should be imported.",
        )

        # for tabular data
        parser.add_argument("--sheet-id", type=str, default=None, help="Google sheet ID used for TABULAR datasource..")
        parser.add_argument(
            "--sheet-name",
            type=str,
            default=None,
            help="Google sheet name used for TABULAR datasource.",
        )
        parser.add_argument("--file-path", type=str, default=None, help="Sheet file path used for TABULAR datasource..")

        # options
        parser.add_argument("-f", "--female", action="store_true", default=False, help="Import data for female races.")
        parser.add_argument(
            "-c",
            "--category",
            type=str,
            default=None,
            help="Import data for the given category (ABSOLUT | VETERAN | SCHOOL).",
        )
        parser.add_argument(
            "-i",
            "--ignore",
            type=str,
            nargs="*",
            default=[],
            help="List of race IDs to ignore during ingestion.",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=None,
            help="Outputs the race data to the given folder path in JSON format.",
        )

    def handle(self, *_, **options):
        logger.debug(f"{options}")

        input_source, year = options["input_source"], options["year"]
        tabular_config = TabularClientConfig(
            sheet_id=options["sheet_id"],
            sheet_name=options["sheet_name"],
            file_path=options["file_path"],
        )
        is_female, category, self._ignored_races, output_path = (
            options["female"],
            options["category"],
            options["ignore"],
            options["output"],
        )

        datasource_or_path, year, category = self._validate_arguments(input_source, year, category)
        ingestor = build_ingestor(datasource_or_path, tabular_config, is_female, category, self._ignored_races)
        for race in ingestor.fetch(year=year, is_female=is_female):
            if output_path and os.path.isdir(output_path):
                file_name = f"{race.race_ids[0]}.json"
                logger.info(f"saving race to {file_name=}")
                with open(os.path.join(output_path, file_name), "w") as file:
                    json.dump(race.to_dict(), file)
                continue

            participants = race.participants
            race.participants = []

            new_race, associated = ingestor.ingest(race)
            new_race, saved = ingestor.save(new_race, associated=associated)

            if not saved:
                db_race = input_race(race)
                if not db_race:
                    continue

                new_race, _ = ingestor.merge(new_race, db_race)
                new_race, saved = ingestor.save(new_race, associated=associated)
                if not saved:
                    logger.warning(f"{race=} was not saved")
                    continue

            for participant in participants:
                new_participant = ingestor.ingest_participant(new_race, participant)
                new_participant, saved = ingestor.save_participant(
                    new_participant, is_disqualified=participant.disqualified
                )

    @staticmethod
    def _validate_arguments(
        maybe_datasource: str,
        year: int | None,
        category: str | None,
    ) -> tuple[Datasource | str, int, str | None]:
        if os.path.isdir(maybe_datasource) or os.path.isfile(maybe_datasource):
            return maybe_datasource, 0, category

        if not year:
            raise ValueError("required value for 'year'")

        if not maybe_datasource or not Datasource.has_value(maybe_datasource):
            raise ValueError(f"invalid datasource={maybe_datasource}")
        if category and maybe_datasource != Datasource.TRAINERAS:
            raise ValueError(f"category filtering is not suported in datasource={maybe_datasource}")
        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")
        return Datasource(maybe_datasource), year, category.upper() if category else None
