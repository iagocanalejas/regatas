#!/usr/bin/env python

import logging
import time
from typing import override

from django.core.management import BaseCommand

from apps.races.models import Flag
from apps.utils import build_client
from rscraping.clients import TrainerasClient
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_FEMALE
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """"""

    @override
    def handle(self, *_, **options):
        client: TrainerasClient = build_client(Datasource.TRAINERAS, GENDER_FEMALE, CATEGORY_ABSOLUT)  # type: ignore
        for flag in Flag.objects.filter(pk__gt=0, verified=False).order_by("id"):
            if len(flag.metadata["datasource"]) == 0:
                # TODO:
                continue
            for datasource in flag.metadata["datasource"]:
                if datasource["datasource_name"] != Datasource.TRAINERAS or "ref_name" in datasource:
                    continue

                logger.info(f"parsing name={flag.name} ref_id={datasource['ref_id']}")
                race_ids = client.get_race_ids_by_flag(datasource["ref_id"])
                for race_id in race_ids:
                    race = client.get_race_by_id(race_id, table=1)
                    if race is not None:
                        if len(race.normalized_names) == 1:
                            logger.info(f"updating flag id={flag.pk} with ref_name={race.normalized_names[0][0]}")
                            datasource["ref_name"] = race.normalized_names[0][0]
                        else:
                            print(race.normalized_names)
                            idx = -1
                            while idx < 0 or idx > len(race.normalized_names):
                                idx = int(input("select name index: "))
                            logger.info(f"updating flag id={flag.pk} with ref_name={race.normalized_names[idx][0]}")
                            datasource["ref_name"] = race.normalized_names[idx][0]
                        break
            flag.save()
            time.sleep(10)
