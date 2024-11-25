#!/usr/bin/env python

import logging
from dataclasses import dataclass
from typing import override

from django.core.management import BaseCommand

from apps.races.models import Race

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """"""

    @override
    def add_arguments(self, parser):
        parser.add_argument("race_id", type=int, help="raceID to merge into.")
        parser.add_argument("race_ids", nargs="*", help="raceIDs to merge into the first one.")

    @override
    def handle(self, *_, **options):
        logger.info(f"{options}")
        config = DedupeConfig.from_args(**options)


@dataclass
class DedupeConfig:
    race: Race
    races: list[Race]

    @classmethod
    def from_args(cls, **options) -> "DedupeConfig":
        race_id, race_ids = options["race_id"], options["race_ids"]
        assert len(race_ids) > 0, "at least one race is required"

        race = Race.objects.get(pk=race_id)
        races = list(Race.objects.filter(pk__in=race_ids))
        assert len(race_ids) == len(races), "not all races were found"

        return cls(race=race, races=races)
