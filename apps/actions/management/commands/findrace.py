#!/usr/bin/env python3

import json
import logging
import os

from django.core.management import BaseCommand

from apps.actions.management.helpers.input import input_race
from apps.actions.management.ingestor import build_ingestor
from rscraping.clients import TabularClientConfig
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file and spreadsheet.

    Usage:
    ------
    python manage.py findrace datasource_or_file [race_id] \
        [-f, --female] \
        [-d, --day DAY] \
        [-o, --output OUTPUT]

    Arguments:
        input_source:
            The name of the Datasource or path to import data from.

        race_ids (optional)
            Races to find and ingest.
            NOTE: This argument is mandatory for Datasource and not supported for local files.

    Options:
        -d, --day DAY
            Day of the race.
            NOTE: This option is only supported for the TRAINERAS datasource.

        -f, --female:
            Import data for female races.

        -o, --output:
            Outputs the race data to the given folder path in JSON format.
    """

    def add_arguments(self, parser):
        parser.add_argument("input_source", type=str, help="The name of the Datasource or path to import data from.")
        parser.add_argument("race_ids", nargs="*", default=None, help="Races to find and ingest.")
        parser.add_argument("-d", "--day", type=int, help="Day of the race.")
        parser.add_argument("-f", "--female", action="store_true", default=False, help="Import data for female races.")
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            default=None,
            help="Outputs the race data to the given folder path in JSON format.",
        )

    def handle(self, *_, **options):
        logger.debug(f"{options}")

        input_source, race_ids = options["input_source"], options["race_ids"]
        is_female, day, output_path = (
            options["female"],
            options["day"],
            options["output"],
        )

        datasource_or_file, race_ids = self._validate_arguments(input_source, race_ids)
        ingestor = build_ingestor(datasource_or_file, TabularClientConfig(), is_female, None, [])
        for race in ingestor.fetch_by_ids(race_ids, day=day):
            logger.info(f"processing {race=}")
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
    def _validate_arguments(maybe_datasource: str, race_ids: list[str]) -> tuple[Datasource | str, list[str]]:
        if os.path.isfile(maybe_datasource):
            return maybe_datasource, []

        if not maybe_datasource or not Datasource.has_value(maybe_datasource):
            raise ValueError(f"invalid datasource={maybe_datasource}")
        if not race_ids or len(race_ids) == 0:
            raise ValueError("required value for 'race_ids'")
        return Datasource(maybe_datasource), race_ids
