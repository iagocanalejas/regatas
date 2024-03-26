#!/usr/bin/env python3

import json
import logging
from dataclasses import dataclass
from typing import override

from django.core.management import BaseCommand

from apps.actions.serializers import ParticipantSerializer, RaceSerializer
from apps.participants.services import ParticipantService
from apps.races.services import MetadataService, RaceService
from pyutils.shortcuts import all_or_none, only_one_not_none
from rscraping.data.functions import sys_print_items
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve races from the database searching by race ID or datasource and ref_id.

    Usage:
        python manage.py find datasource_or_race [REF_ID]

    Arguments:
        datasource_or_race:
            The name of the Datasource or race ID to retrieve.
        ref_id:
            The reference ID to search for.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("datasource_or_race", help="The name of the Datasource or path to import data from.")
        parser.add_argument("ref_id", nargs="?", default=None, help="Races to find and ingest.")

    @override
    def handle(self, *_, **options):
        logger.debug(f"{options}")
        config = FindConfig.from_args(**options)

        races = []
        if config.race_id:
            race = RaceService.get_race_or_none(config.race_id)
            if not race:
                logger.error(f"no race found for race_id={config.race_id}")
            races = [race] if race else []
        if config.ref_id and config.datasource:
            races = MetadataService.get_races(config.datasource, config.ref_id)

        for race in races:
            data = RaceSerializer(race).data
            participants = ParticipantService.get_by_race(race)
            data["participants"] = ParticipantSerializer(participants, many=True).data  # pyright: ignore
            sys_print_items([json.dumps(data)])


@dataclass
class FindConfig:
    race_id: int | None = None
    datasource: Datasource | None = None
    ref_id: str | None = None

    @classmethod
    def from_args(cls, **options) -> "FindConfig":
        datasource_or_race, ref_id = options["datasource_or_race"], options["ref_id"]

        if datasource_or_race.isdigit():
            datasource, race_id = None, int(datasource_or_race)
        else:
            if not Datasource.has_value(datasource_or_race):
                raise ValueError(f"Invalid datasource: {datasource_or_race}")
            datasource, race_id = Datasource(datasource_or_race), None

        if not only_one_not_none(race_id, ref_id):
            raise ValueError("Only one of 'race_id' and 'ref_id' must be provided.")
        if not all_or_none(datasource, ref_id):
            raise ValueError("Both 'datasource' and 'ref_id' must be provided.")

        return cls(
            race_id=race_id,
            datasource=Datasource(datasource) if datasource else None,
            ref_id=ref_id,
        )
