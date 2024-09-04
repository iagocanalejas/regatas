#!/usr/bin/env python3

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
from typing import override

from django.core.management import BaseCommand

from apps.actions.management.digester import Digester, DigesterProtocol, build_digester
from apps.actions.management.helpers.input import input_race
from apps.actions.management.ingester import build_ingester
from apps.entities.models import Entity
from apps.entities.services import EntityService
from apps.races.models import Race
from apps.utils import build_client
from pyutils.shortcuts import only_one_not_none
from rscraping.clients import TabularClientConfig
from rscraping.data.constants import (
    CATEGORY_ABSOLUT,
    CATEGORY_SCHOOL,
    CATEGORY_VETERAN,
    GENDER_ALL,
    GENDER_FEMALE,
    GENDER_MALE,
    GENDER_MIX,
)
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file or spreadsheet.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("input_source", type=str, help="name of the Datasource or path to import data from.")
        parser.add_argument("race_ids", nargs="*", help="raceIDs to find in the source and ingest.")
        parser.add_argument("-c", "--club", type=int, help="clubID for which races should be imported.")
        parser.add_argument("-e", "--entity", type=int, help="entityID for which races should be imported.")
        parser.add_argument("-f", "--flag", type=int, help="flagID for which races should be imported.")

        parser.add_argument(
            "-y",
            "--year",
            type=str,
            help="year for which races should be imported, 'all' to import from the source beginnig.",
        )
        parser.add_argument(
            "-sy",
            "--start-year",
            type=int,
            help="year for which we should start processing years. Only used with year='all'.",
        )

        # for tabular data
        parser.add_argument("--sheet-id", type=str, help="google-sheet ID used for TABULAR datasource.")
        parser.add_argument("--sheet-name", type=str, help="google-sheet name used for TABULAR datasource.")
        parser.add_argument("--file-path", type=str, help="sheet file path used for TABULAR datasource.")

        # options
        parser.add_argument("-t", "--table", type=int, help="table of the race for multipage races.")
        parser.add_argument("-g", "--gender", type=str, default=GENDER_MALE, help="gender filter.")
        parser.add_argument("-ca", "--category", type=str, default=CATEGORY_ABSOLUT, help="category filter.")
        parser.add_argument(
            "-i",
            "--ignore",
            type=str,
            nargs="*",
            default=[],
            help="raceIDs to ignore during ingestion.",
        )
        parser.add_argument(
            "-w",
            "--last-weekend",
            action="store_true",
            default=False,
            help="fetches the races for the last weekend.",
        )
        parser.add_argument(
            "--force-gender",
            action="store_true",
            default=False,
            help="forces the gender to match.",
        )
        parser.add_argument(
            "--force-category",
            action="store_true",
            default=False,
            help="forces the category to match.",
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

        client = build_client(config.datasource, config.gender, config.tabular_config, config.category)
        ingester = build_ingester(client=client, path=config.path, ignored_races=config.ignored_races)
        digester = build_digester(
            client=client,
            path=config.path,
            force_gender=config.force_gender,
            force_category=config.force_category,
        )

        # compute years to scrape
        if config.year == ScrapeConfig.ALL_YEARS:
            start = ingester.client.FEMALE_START if config.gender == GENDER_FEMALE else ingester.client.MALE_START
            years = range(config.start_year if config.start_year else start, datetime.now().year + 1)
        else:
            years = [config.year] if config.year else []

        # fetch races depending on the configuration
        if config.entity and config.year:
            races = chain(*[ingester.fetch_by_entity(entity=config.entity, year=year) for year in years])
        elif config.club_id and config.year:
            races = chain(*[ingester.fetch_by_club(club_id=config.club_id, year=year) for year in years])
        elif config.flag_id:
            races = ingester.fetch_by_flag(flag_id=config.flag_id)
        elif config.race_ids:
            races = ingester.fetch_by_ids(race_ids=config.race_ids, table=config.table)
        elif config.year:
            races = chain(*[ingester.fetch(year=year) for year in years])
        elif config.last_weekend:
            races = ingester.fetch_last_weekend()
        else:
            raise ValueError("invalid state")

        for race in races:
            if config.output_path and os.path.isdir(config.output_path):
                file_name = f"{race.race_ids[0]}.json"
                logger.info(f"saving race to {file_name=}")
                with open(os.path.join(config.output_path, file_name), "w") as file:
                    json.dump(race.to_dict(), file)
                continue

            ingest_race(digester, race)


@dataclass
class ScrapeConfig:
    ALL_YEARS = -1

    tabular_config: TabularClientConfig

    datasource: Datasource | None = None
    path: str | None = None
    race_ids: list[str] = field(default_factory=list)
    year: int | None = None
    entity: Entity | None = None
    club_id: str | None = None
    flag_id: str | None = None

    category: str = CATEGORY_ABSOLUT
    gender: str = GENDER_MALE
    table: int | None = None
    start_year: int | None = None

    last_weekend: bool = False
    force_gender: bool = False
    force_category: bool = False
    ignored_races: list[str] = field(default_factory=list)
    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "ScrapeConfig":
        input_source, race_ids, year, club_id, entity_id, flag_id = (
            options["input_source"],
            options["race_ids"],
            options["year"],
            options["club"],
            options["entity"],
            options["flag"],
        )
        tabular_config = TabularClientConfig(
            sheet_id=options["sheet_id"],
            sheet_name=options["sheet_name"],
            file_path=options["file_path"],
        )
        category, gender, table, start_year, last_weekend = (
            options["category"],
            options["gender"],
            options["table"],
            options["start_year"],
            options["last_weekend"],
        )
        force_gender, force_category, ignored_races, output_path = (
            options["force_gender"],
            options["force_category"],
            options["ignore"],
            options["output"],
        )

        if os.path.isfile(input_source) or os.path.isdir(input_source):
            datasource, path = None, input_source
        else:
            if not input_source or not Datasource.has_value(input_source):
                raise ValueError(f"Invalid datasource: {input_source}")
            datasource, path = Datasource(input_source), None

        if not gender or gender.upper() not in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX]:
            raise ValueError(f"invalid {gender=}")

        has_races = True if len(race_ids) > 0 else None
        if not only_one_not_none(year, has_races, flag_id, last_weekend or None):
            raise ValueError("only one of 'year', 'race_ids', 'flag' and 'last_weekend' can be provided")
        if not year and not club_id and not entity_id and not flag_id and not last_weekend and len(race_ids) == 0:
            raise ValueError(
                "required value for 'race_ids' or 'club' or 'entity' or 'flag' or 'year' or 'last_weekend'"
            )
        if (club_id or entity_id) and not year:
            raise ValueError("'year' is required when 'club' is provided")
        if (club_id or entity_id) and datasource != Datasource.TRAINERAS:
            raise ValueError("'club' is only supported in TRAINERAS datasource")
        if flag_id and datasource != Datasource.TRAINERAS:
            raise ValueError("'flag' is only supported in TRAINERAS datasource")

        year = cls.parse_year(year)

        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")
        if table and len(race_ids) != 1:
            raise ValueError("day filtering is only supported for one race_id")

        entity = EntityService.get_entity_or_none(entity_id) if entity_id else None
        if entity_id and not entity:
            raise ValueError(f"invalid {entity_id=}")

        return cls(
            tabular_config=tabular_config,
            datasource=datasource,
            path=path,
            race_ids=race_ids,
            year=year,
            entity=entity,
            club_id=club_id,
            flag_id=flag_id,
            category=category.upper() if category else CATEGORY_ABSOLUT,
            gender=gender.upper(),
            table=table,
            start_year=start_year,
            last_weekend=last_weekend,
            force_gender=force_gender,
            force_category=force_category,
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


def ingest_race(digester: DigesterProtocol, race: RSRace):
    participants = race.participants
    race.participants = []

    new_race, race_status = digest_race(digester, race)
    if not new_race:
        logger.warning(f"{race=} was not saved")
        return

    for participant in participants:
        new_participant, status = digester.ingest_participant(new_race, participant)
        if status == Digester.Status.NEW or status == Digester.Status.MERGED:
            new_participant, status = digester.save_participant(
                new_participant,
                race_status=race_status,
                participant_status=status,
            )
        if new_participant.pk and participant.penalty:
            _ = digester.save_penalty(new_participant, participant.penalty)

    if race.race_notes:
        logger.warning(f"{race.date} :: {race.race_notes}")


def digest_race(digester: DigesterProtocol, race: RSRace) -> tuple[Race | None, Digester.Status]:
    try:
        new_race, associated, status = digester.ingest(race)
        new_race, status = digester.save(new_race, status, associated=associated)
        if not status.is_saved():
            db_race = input_race(race)
            if not db_race:
                return None, Digester.Status.IGNORE

            new_race, status = digester.merge(new_race, db_race, status)
            new_race, status = digester.save(new_race, status, associated=associated)
            if not status.is_saved():
                return None, Digester.Status.IGNORE
        return new_race, status
    except AssertionError as e:
        logger.error(e)
        return None, Digester.Status.IGNORE
    except KeyboardInterrupt as e:
        with open(f"{race.race_ids[0]}.json", "w") as f:
            json.dump(race.to_dict(), f, ensure_ascii=False)
        raise e
