#!/usr/bin/env python3

import logging
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from typing import override

from django.core.management import BaseCommand
from django.db.models import Exists, OuterRef, Q

from apps.actions.management.digester import build_digester
from apps.actions.management.digester._protocol import DigesterProtocol
from apps.actions.management.ingester import build_ingester
from apps.races.models import Flag, Race
from apps.races.services import MetadataService
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
from rscraping.data.models import Race as RSRace

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
            "--check-participants",
            action="store_true",
            default=False,
            help="checks if the number of participants matches.",
        )
        parser.add_argument(
            "--only-new",
            action="store_true",
            default=False,
            help="scrape only newer races than the last one in database.",
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

    @override
    def handle(self, *_, **options):
        logger.debug(f"{options}")
        config = RecheckConfig.from_args(**options)

        client = build_client(config.datasource, config.gender, category=config.category)
        ingester = build_ingester(client=client)
        digester = build_digester(client=client, force_gender=config.force_gender, force_category=config.force_category)

        flag_ids = [config.flag_id] if config.flag_id else None
        if flag_ids is None:
            flag_ids = self._get_flag_ids(datasource=config.datasource, only_new=config.only_new)
        races = chain(*[ingester.fetch_by_flag(flag_id=flag_id, only_new=config.only_new) for flag_id in flag_ids])

        checked_flags = set()
        for rs_race in races:
            new_race = check_race(digester, rs_race, check_participants=config.check_participants)
            if new_race and new_race.flag not in checked_flags:
                flag = new_race.flag
                flag.last_checked = datetime.now()
                flag.save()

                logger.info(f"updating last_checked value for {flag=}")
                checked_flags.add(flag)

    def _get_flag_ids(self, datasource: Datasource, only_new: bool = False) -> Generator[str]:
        last_month = datetime.now().replace(month=datetime.now().month - 1)
        flags = Flag.objects.filter(
            Q(last_checked__lte=last_month) | Q(last_checked__isnull=True),
            metadata__datasource__contains=[{"datasource_name": datasource.value}],
        )
        if only_new:
            flags = flags.filter(~Exists(Race.objects.filter(flag=OuterRef("pk"), date__year=datetime.now().year)))

        for flag in flags:
            for value in flag.metadata["datasource"]:
                if value["datasource_name"] == datasource.value:
                    yield value["ref_id"]


@dataclass
class RecheckConfig:
    datasource: Datasource
    flag_id: str | None = None

    category: str = CATEGORY_ABSOLUT
    gender: str = GENDER_MALE

    check_participants: bool = False
    only_new: bool = False
    force_gender: bool = False
    force_category: bool = False

    @classmethod
    def from_args(cls, **options) -> "RecheckConfig":
        datasource, flag_id, category, gender, check_participants, only_new, force_gender, force_category = (
            options["datasource"],
            options["flag"],
            options["category"],
            options["gender"],
            options["check_participants"],
            options["only_new"],
            options["force_gender"],
            options["force_category"],
        )

        assert datasource and Datasource.has_value(datasource), f"Invalid datasource: {datasource}"
        datasource = Datasource(datasource)

        # fmt: off
        assert not gender or gender.upper() in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX], f"invalid {gender=}"  # noqa: E501
        assert not category or category.upper() in [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL], f"invalid {category=}"  # noqa: E501
        assert not flag_id or datasource == Datasource.TRAINERAS, "'flag' is only supported in TRAINERAS datasource"
        # fmt: on

        return cls(
            datasource=datasource,
            flag_id=flag_id,
            category=category.upper() if category else CATEGORY_ABSOLUT,
            gender=gender.upper(),
            check_participants=check_participants,
            only_new=only_new,
            force_gender=force_gender,
            force_category=force_category,
        )


def check_race(digester: DigesterProtocol, rs_race: RSRace, check_participants: bool) -> Race | None:
    if check_participants:
        assert Datasource.has_value(rs_race.datasource), f"invalid {rs_race.datasource=}"
        assert len(rs_race.race_ids) == 1, f"invalid number for references {rs_race.race_ids}"

        race = MetadataService.get_race_or_none(
            datasource=Datasource(rs_race.datasource),
            ref_id=rs_race.race_ids[0],
            day=rs_race.day,
            prefetch=["participants"],
        )

        if race:
            same_participants = race.participants.count() == len(rs_race.participants)
            assert same_participants, f"invalid number of participants for {race=}"
            return

    new_race, _ = ingest_race(digester, rs_race)
    return new_race
