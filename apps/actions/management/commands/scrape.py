#!/usr/bin/env python3

import json
import logging
import os
from collections.abc import Generator
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
from apps.participants.services import ParticipantService
from apps.races.models import Flag, Race, Trophy
from apps.schemas import MetadataBuilder
from apps.utils import build_client
from pyutils.shortcuts import only_one_not_none
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

_notes: list[str] = []


class Command(BaseCommand):
    help = """
    Retrieve and process race data from a web datasource, JSON file or spreadsheet.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("datasource", type=str, help="name of the Datasource to import data from.")
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
            "--save-old",
            action="store_true",
            default=False,
            help="automatically saves the races before 2003 without asking.",
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

        client = build_client(config.datasource, config.gender, config.category)
        ingester = build_ingester(client=client, ignored_races=config.ignored_races)
        digester = build_digester(
            client=client,
            force_gender=config.force_gender,
            force_category=config.force_category,
            save_old=config.save_old,
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

        try:
            self.run(config, digester, races)
        except Exception as e:
            for note in _notes:
                logger.warning(note)
            raise e
        finally:
            for note in _notes:
                logger.warning(note)

    def run(self, config: "ScrapeConfig", digester: DigesterProtocol, races: chain[RSRace] | Generator[RSRace]):
        flags: set[Flag] = set()
        hints: dict[str, tuple[Flag, Trophy]] = {}
        for race in races:
            if config.output_path and os.path.isdir(config.output_path):
                file_name = f"{race.race_ids[0]}.json"
                logger.info(f"saving race to {file_name=}")
                with open(os.path.join(config.output_path, file_name), "w") as file:
                    json.dump(race.to_dict(), file)
                continue

            new_race, _ = ingest_race(digester, race, hint=hints.get(race.name, None))
            if new_race and new_race.flag:
                flags.add(new_race.flag)
            if new_race and race.name not in hints:
                hints[race.name] = (new_race.flag, new_race.trophy)

        if config.flag_id and config.datasource == Datasource.TRAINERAS and len(flags) == 1:
            flag = flags.pop()
            logger.info(f"adding metadata to {flag}")
            if len(flag.get_datasources(config.datasource, config.flag_id)) == 0:
                flag.add_metadata(
                    MetadataBuilder()
                    .ref_id(config.flag_id)
                    .datasource_name(config.datasource)
                    .values("details_page", f"https://traineras.es/banderas/{config.flag_id}")
                    .build()
                )
                flag.save()
                logger.info(f"{flag=} metadata has been updated")


@dataclass
class ScrapeConfig:
    ALL_YEARS = -1

    datasource: Datasource | None = None
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
    save_old: bool = False
    ignored_races: list[str] = field(default_factory=list)
    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "ScrapeConfig":
        input_source, race_ids, year, club_id, entity_id, flag_id = (
            options["datasource"],
            options["race_ids"],
            options["year"],
            options["club"],
            options["entity"],
            options["flag"],
        )
        category, gender, table, start_year, last_weekend = (
            options["category"],
            options["gender"],
            options["table"],
            options["start_year"],
            options["last_weekend"],
        )
        force_gender, force_category, save_old, ignored_races, output_path = (
            options["force_gender"],
            options["force_category"],
            options["save_old"],
            options["ignore"],
            options["output"],
        )

        assert input_source and Datasource.has_value(input_source), f"invalid {input_source=}"
        datasource = Datasource(input_source)

        # fmt: off
        has_races = True if len(race_ids) > 0 else None
        assert only_one_not_none(year, has_races, flag_id, last_weekend or None), "only one of 'year', 'race_ids', 'flag' and 'last_weekend' can be provided"  # noqa: E501
        assert year or club_id or entity_id or flag_id or last_weekend or len(race_ids) > 0, "required value for 'race_ids' or 'club' or 'entity' or 'flag' or 'year' or 'last_weekend'"  # noqa: E501
        assert not club_id and not entity_id or year, "'year' is required when 'club' is provided"
        assert not club_id and not entity_id or datasource == Datasource.TRAINERAS, "'club' is only supported in TRAINERAS datasource"  # noqa: E501
        assert not flag_id or datasource == Datasource.TRAINERAS, "'flag' is only supported in TRAINERAS datasource"
        assert not gender or gender.upper() in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX], f"invalid {gender=}"  # noqa: E501
        assert not category or category.upper() in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL], f"invalid {category=}"  # noqa: E501
        assert not table or len(race_ids) == 1, "table filtering is only supported ingesting one race"
        assert not entity_id or entity_id.isdigit(), f"invalid {entity_id=}"
        # fmt: on

        year = cls.parse_year(year)

        entity = EntityService.get_entity_or_none(entity_id) if entity_id else None
        assert not entity_id or entity, f"invalid {entity_id=}"

        return cls(
            datasource=datasource,
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
            save_old=save_old,
            ignored_races=ignored_races,
            output_path=output_path,
        )

    @classmethod
    def parse_year(cls, year: str | None) -> int | None:
        if not year:
            return None
        if year == "all":
            return cls.ALL_YEARS

        assert year.isdigit(), f"invalid {year=}"

        y = int(year)
        assert y > 1950, f"invalid {year=}"
        assert y < 2100, f"invalid {year=}"

        return y


def ingest_race(
    digester: DigesterProtocol,
    race: RSRace,
    hint: tuple[Flag, Trophy] | None = None,
) -> tuple[Race | None, Digester.Status]:
    participants = race.participants
    race.participants = []

    try:
        new_race, race_status = digest_race(digester, race, hint=hint)
    except Exception as e:
        race.participants = participants
        with open(f"{race.race_ids[0]}.json", "w") as f:
            json.dump(race.to_dict(), f, ensure_ascii=False)
        raise e

    if not new_race:
        logger.warning(f"{race=} was not saved")
        return None, Digester.Status.IGNORE

    participant_names = [p.participant for p in participants]
    for participant in participants:
        can_be_branch_team = ParticipantService.can_be_branch(participant.participant, participant_names)
        can_be_branch_team = new_race.league is None and can_be_branch_team
        new_participant, status = digester.ingest_participant(new_race, participant, can_be_branch=can_be_branch_team)
        if status == Digester.Status.NEW or status == Digester.Status.MERGED:
            new_participant, status = digester.save_participant(
                new_participant,
                race_status=race_status,
                participant_status=status,
            )
        if new_participant.pk and participant.penalty:
            _ = digester.save_penalty(new_participant, participant.penalty, race.race_notes)

    if race.race_notes:
        logger.warning(f"{race.date} :: {race.race_notes}")
        _notes.append(f"{race.date} :: {race.race_notes}")

    return new_race, race_status


def digest_race(
    digester: DigesterProtocol,
    race: RSRace,
    hint: tuple[Flag, Trophy] | None = None,
) -> tuple[Race | None, Digester.Status]:
    try:
        new_race, associated, status = digester.ingest(race, hint=hint)
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
