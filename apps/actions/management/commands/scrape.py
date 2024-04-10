#!/usr/bin/env python3

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
from typing import override

from django.core.management import BaseCommand

from apps.actions.management.helpers.input import input_race
from apps.actions.management.ingestor import IngestorProtocol, build_ingestor
from apps.entities.models import Entity
from apps.entities.services import EntityService
from apps.races.models import Race
from pyutils.shortcuts import only_one_not_none
from rscraping.clients import TabularClientConfig
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace

from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file or spreadsheet.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("input_source", type=str, help="name of the Datasource or path to import data from.")
        parser.add_argument("race_ids", nargs="*", help="race IDs to find in the source and ingest.")
        parser.add_argument("--club", type=int, help="club for which races should be imported.")
        parser.add_argument("--flag", type=int, help="flag for which races should be imported.")

        parser.add_argument(
            "--year",
            type=str,
            help="year for which races should be imported, 'all' to import from the source beginnig.",
        )
        parser.add_argument(
            "--start-year",
            type=int,
            help="year for which we should start processing years. Only used with year='all'.",
        )

        # for tabular data
        parser.add_argument("--sheet-id", type=str, help="google-sheet ID used for TABULAR datasource.")
        parser.add_argument("--sheet-name", type=str, help="google-sheet name used for TABULAR datasource.")
        parser.add_argument("--file-path", type=str, help="sheet file path used for TABULAR datasource.")

        # options
        parser.add_argument("-t", "--table", type=int, help="rable of the race for multipage races.")
        parser.add_argument("-f", "--female", action="store_true", default=False, help="female races.")
        parser.add_argument("-c", "--category", type=str, help="one of (ABSOLUT | VETERAN | SCHOOL).")
        parser.add_argument(
            "-i",
            "--ignore",
            type=str,
            nargs="*",
            default=[],
            help="race IDs to ignore during ingestion.",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
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
            is_female=config.is_female,
            tabular_config=config.tabular_config,
            category=config.category,
            ignored_races=config.ignored_races,
        )

        # compute years to scrape
        if config.year == ScrapeConfig.ALL_YEARS:
            start = ingestor.client.FEMALE_START if config.is_female else ingestor.client.MALE_START
            years = range(config.start_year if config.start_year else start, datetime.now().year + 1)
        else:
            years = [config.year] if config.year else []

        # fetch races depending on the configuration
        if config.club and config.year:
            races = chain(*[ingestor.fetch_by_club(config.club, year=year) for year in years])
        elif config.flag:
            races = ingestor.fetch_by_flag(config.flag, is_female=config.is_female)
        elif config.race_ids:
            races = ingestor.fetch_by_ids(config.race_ids, table=config.table)
        elif config.year:
            races = chain(*[ingestor.fetch(year=year, is_female=config.is_female) for year in years])
        else:
            raise ValueError("invalid state")

        for race in races:
            if config.output_path and os.path.isdir(config.output_path):
                file_name = f"{race.race_ids[0]}.json"
                logger.info(f"saving race to {file_name=}")
                with open(os.path.join(config.output_path, file_name), "w") as file:
                    json.dump(race.to_dict(), file)
                continue

            participants = race.participants
            race.participants = []

            new_race = self.ingest_race(ingestor, race)
            if not new_race:
                logger.warning(f"{race=} was not saved")
                continue

            for participant in participants:
                new_participant, new_or_updated = ingestor.ingest_participant(new_race, participant)
                if new_or_updated:
                    new_participant, _ = ingestor.save_participant(
                        new_participant, is_disqualified=participant.disqualified
                    )

    def ingest_race(self, ingestor: IngestorProtocol, race: RSRace) -> Race | None:
        try:
            new_race, associated = ingestor.ingest(race)
            new_race, saved = ingestor.save(new_race, associated=associated)
            if not saved:
                db_race = input_race(race)
                if not db_race:
                    return None

                new_race, _ = ingestor.merge(new_race, db_race)
                new_race, saved = ingestor.save(new_race, associated=associated)
                if not saved:
                    return None
            return new_race
        except StopProcessing as e:
            logger.error(e)
            return None
        except KeyboardInterrupt as e:
            with open(f"{race.race_ids[0]}.json", "w") as f:
                json.dump(race.to_dict(), f, ensure_ascii=False)
            raise e


@dataclass
class ScrapeConfig:
    ALL_YEARS = -1

    tabular_config: TabularClientConfig

    datasource: Datasource | None = None
    path: str | None = None
    race_ids: list[str] = field(default_factory=list)
    year: int | None = None
    club: Entity | None = None
    flag: str | None = None

    category: str | None = None
    is_female: bool = False
    table: int | None = None
    start_year: int | None = None

    ignored_races: list[str] = field(default_factory=list)
    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "ScrapeConfig":
        input_source, race_ids, year, club_id, flag_id = (
            options["input_source"],
            options["race_ids"],
            options["year"],
            options["club"],
            options["flag"],
        )
        tabular_config = TabularClientConfig(
            sheet_id=options["sheet_id"],
            sheet_name=options["sheet_name"],
            file_path=options["file_path"],
        )
        category, is_female, table, start_year, ignored_races, output_path = (
            options["category"],
            options["female"],
            options["table"],
            options["start_year"],
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
        if not only_one_not_none(year, has_races, flag_id):
            raise ValueError("only one of 'year', 'race_ids', 'flag' can be provided")
        if not year and not club_id and not flag_id and len(race_ids) == 0:
            raise ValueError("required value for 'race_ids' or 'club' or 'flag' or 'year'")
        if club_id and not year:
            raise ValueError("'year' is required when 'club' is provided")
        if club_id and datasource != Datasource.TRAINERAS:
            raise ValueError("'club' is only supported in TRAINERAS datasource")
        if flag_id and datasource != Datasource.TRAINERAS:
            raise ValueError("'flag' is only supported in TRAINERAS datasource")

        year = cls.parse_year(year)

        if category and datasource != Datasource.TRAINERAS:
            raise ValueError(f"category filtering is not suported in {datasource=}")
        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")
        if table and len(race_ids) != 1:
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
            flag=flag_id,
            category=category.upper() if category else None,
            is_female=is_female,
            table=table,
            start_year=start_year,
            ignored_races=ignored_races,
            output_path=output_path,
        )

    @classmethod
    def parse_year(cls, year: str | None) -> int | None:
        if year:
            if year == "all":
                return cls.ALL_YEARS
            elif year.isdigit():
                y = int(year)
                if y < 1950 or y > 2100:
                    raise ValueError(f"invalid {year=}")
                return y
            else:
                raise ValueError(f"invalid {year=}")
        return None
