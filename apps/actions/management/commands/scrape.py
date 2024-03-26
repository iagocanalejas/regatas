#!/usr/bin/env python3

import json
import logging
import os
from dataclasses import dataclass, field
from typing import override

from django.core.management import BaseCommand

from apps.actions.management.helpers.input import input_race
from apps.actions.management.ingestor import build_ingestor
from apps.entities.models import Entity
from apps.entities.services import EntityService
from pyutils.shortcuts import only_one_not_none
from rscraping.clients import TabularClientConfig
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file or spreadsheet.

    Usage:
        python manage.py scrape input_source [RACE_ID [RACE_ID ...]] \
            [--year YEAR] \
            [-f, --female] \
            [-c, --category CATEGORY] \
            [-d, --day DAY] \
            [--sheet-id SHEET_ID] \
            [--sheet-name SHEET_NAME] \
            [--file-path FILE_PATH] \
            [-i, --ignore ID [ID ...]] \
            [-o, --output OUTPUT]

    Arguments:
        input_source:
            The name of the Datasource or path to import data.

        race_ids (optional)
            Races to find and ingest.

    Options:
        --year YEAR
            The year for which races should be imported.

        --club CLUB
            The club for which races should be imported.

        -f, --female:
            Import data for female races.

        -c, --category:
            Import data for the given category (ABSOLUT | VETERAN | SCHOOL).
            NOTE: This option is only supported for the TRAINERAS datasource.

        -d, --day DAY
            Day of the race.
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

    NOTE: One of 'year' | 'race_ids' is required and they are mutually exclusive.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("input_source", type=str, help="The name of the Datasource or path to import data from.")
        parser.add_argument("race_ids", nargs="*", default=None, help="Races to find and ingest.")
        parser.add_argument("--year", type=int, default=None, help="The year for which races should be imported.")
        parser.add_argument("--club", type=int, default=None, help="The club for which races should be imported.")

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
        parser.add_argument("-d", "--day", type=int, help="Day of the race.")
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

    @override
    def handle(self, *_, **options):
        logger.debug(f"{options}")
        config = ScrapeConfig.from_args(**options)

        source = config.datasource or config.path
        assert isinstance(source, (Datasource, str))
        ingestor = build_ingestor(
            source=source,
            tabular_config=config.tabular_config,
            is_female=config.is_female,
            category=config.category,
            ignored_races=config.ignored_races,
        )

        races = []
        if config.club and config.year:
            races = ingestor.fetch_by_club(config.club, year=config.year)
        elif config.race_ids:
            races = ingestor.fetch_by_ids(config.race_ids, day=config.day)
        elif config.year:
            races = ingestor.fetch(year=config.year, is_female=config.is_female)

        for race in races:
            if config.output_path and os.path.isdir(config.output_path):
                file_name = f"{race.race_ids[0]}.json"
                logger.info(f"saving race to {file_name=}")
                with open(os.path.join(config.output_path, file_name), "w") as file:
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


@dataclass
class ScrapeConfig:
    tabular_config: TabularClientConfig

    datasource: Datasource | None = None
    path: str | None = None
    race_ids: list[str] = field(default_factory=list)
    year: int | None = None
    club: Entity | None = None

    category: str | None = None
    is_female: bool = False
    day: int | None = None

    ignored_races: list[str] = field(default_factory=list)
    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "ScrapeConfig":
        input_source, race_ids, year, club_id = (
            options["input_source"],
            options["race_ids"],
            options["year"],
            options["club"],
        )
        tabular_config = TabularClientConfig(
            sheet_id=options["sheet_id"],
            sheet_name=options["sheet_name"],
            file_path=options["file_path"],
        )
        category, is_female, day, ignored_races, output_path = (
            options["category"],
            options["female"],
            options["day"],
            options["ignore"],
            options["output"],
        )

        if os.path.isfile(input_source) or os.path.isdir(input_source):
            datasource, path = None, input_source
        else:
            if not input_source or not Datasource.has_value(input_source):
                raise ValueError(f"Invalid datasource: {input_source}")
            datasource, path = Datasource(input_source), None

        has_races = True if len(race_ids) > 0 else None
        if not only_one_not_none(year, has_races):
            raise ValueError("only one of 'year', 'race_ids' can be provided")
        if not year and not club_id and len(race_ids) == 0:
            raise ValueError("required value for 'race_ids' or 'club' or 'year'")
        if club_id and not year:
            raise ValueError("'year' is required when 'club' is provided")
        if club_id and datasource != Datasource.TRAINERAS:
            raise ValueError("'club' is only supported in TRAINERAS datasource")

        # TODO: allow year=all
        if year and year < 1950 or year > 2100:
            raise ValueError(f"invalid {year=}")
        if category and datasource != Datasource.TRAINERAS:
            raise ValueError(f"category filtering is not suported in {datasource=}")
        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")
        if day and len(race_ids) != 1:
            raise ValueError("day filtering is only supported for one race_id")

        club = EntityService.get_entity_or_none(club_id) if club_id else None
        if club_id and not club:
            raise ValueError(f"invalid {club_id=}")

        return cls(
            tabular_config=tabular_config,
            datasource=datasource,
            path=path,
            race_ids=race_ids,
            year=year,
            club=club,
            category=category.upper() if category else None,
            is_female=is_female,
            day=day,
            ignored_races=ignored_races,
            output_path=output_path,
        )
