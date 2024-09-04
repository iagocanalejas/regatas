#!/usr/bin/env python3

import logging
from collections.abc import Generator
from dataclasses import dataclass
from itertools import chain
from typing import override

from django.core.management import BaseCommand

from apps.actions.management.digester import build_digester
from apps.actions.management.ingester import build_ingester
from apps.races.models import Flag
from apps.utils import build_client
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

from .scrape import ingest_race

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Check already imported flags to find new races.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("datasource", type=str, help="name of the Datasource or path to import data from.")
        parser.add_argument("-f", "--flag", type=int, help="flagID for which races should be imported.")

        parser.add_argument("-g", "--gender", type=str, default=GENDER_MALE, help="gender filter.")
        parser.add_argument("-ca", "--category", type=str, default=CATEGORY_ABSOLUT, help="category filter.")

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

    @override
    def handle(self, *_, **options):
        logger.debug(f"{options}")
        config = RecheckConfig.from_args(**options)

        client = build_client(config.datasource, config.gender, category=config.category)
        ingester = build_ingester(client=client)
        digester = build_digester(client=client, force_gender=config.force_gender, force_category=config.force_category)

        flag_ids = [config.flag_id] if config.flag_id else self._get_flag_ids(datasource=config.datasource)
        races = chain(*[ingester.fetch_by_flag(flag_id=flag_id) for flag_id in flag_ids])

        for race in races:
            ingest_race(digester, race)

    def _get_flag_ids(self, datasource: Datasource) -> Generator[str]:
        for flag in Flag.objects.filter(metadata__datasource__contains=[{"datasource_name": datasource.value}]):
            for value in flag.metadata["datasource"]:
                if value["datasource_name"] == datasource.value:
                    yield value["ref_id"]


@dataclass
class RecheckConfig:
    datasource: Datasource
    flag_id: str | None = None

    category: str = CATEGORY_ABSOLUT
    gender: str = GENDER_MALE

    force_gender: bool = False
    force_category: bool = False

    @classmethod
    def from_args(cls, **options) -> "RecheckConfig":
        datasource, flag_id, category, gender, force_gender, force_category = (
            options["datasource"],
            options["flag"],
            options["category"],
            options["gender"],
            options["force_gender"],
            options["force_category"],
        )

        if not datasource or not Datasource.has_value(datasource):
            raise ValueError(f"Invalid datasource: {datasource}")
        datasource = Datasource(datasource)

        if not gender or gender.upper() not in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX]:
            raise ValueError(f"invalid {gender=}")

        if flag_id and datasource != Datasource.TRAINERAS:
            raise ValueError("'flag' is only supported in TRAINERAS datasource")

        if category and category.upper() not in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]:
            raise ValueError(f"invalid {category=}")

        return cls(
            datasource=datasource,
            flag_id=flag_id,
            category=category.upper() if category else CATEGORY_ABSOLUT,
            gender=gender.upper(),
            force_gender=force_gender,
            force_category=force_category,
        )
