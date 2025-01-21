#!/usr/bin/env python3

import logging
import time
from collections.abc import Generator
from datetime import datetime

from django.core.management import BaseCommand
from django.db.models import QuerySet

from apps.actions.management.digester._digester import Digester
from apps.participants.models import Participant
from apps.races.models import Flag, Race
from pyutils.shortcuts import clean_dict
from rscraping.clients import TrainerasClient
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_SCHOOL, GENDER_ALL, GENDER_MIX
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("fixes4.log")
formatter = logging.Formatter("%(levelname)s %(asctime)s %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Command(BaseCommand):
    client = TrainerasClient(source=Datasource.TRAINERAS, gender=GENDER_MIX, category=CATEGORY_ABSOLUT)
    digester = Digester(client, force_gender=True, force_category=True)

    def filter_races(
        self,
        races: QuerySet[Race],
        datasource: Datasource,
        race_refs: list[str],
    ) -> Generator[tuple[Race, str]]:
        for race in races:
            if race.gender != GENDER_ALL:
                continue
            for ds in race.metadata["datasource"]:
                if ds["datasource_name"] == datasource.value and ds["ref_id"] in race_refs:
                    yield (race, ds["ref_id"])

    def filter_flags(self, flags: QuerySet[Flag], datasource: Datasource) -> Generator[tuple[Flag, str]]:
        for flag in flags:
            for ds in flag.metadata["datasource"]:
                if ds["datasource_name"] == datasource.value:
                    yield (flag, ds["ref_id"])

    def handle(self, *_, **options):
        logger.info(f"{options}")
        assert isinstance(self.client, TrainerasClient)

        datasource = Datasource.TRAINERAS
        flags = Flag.objects.filter(
            pk__in=Race.objects.filter(gender=GENDER_ALL).values_list("flag_id", flat=True),
            metadata__datasource__contains=[{"datasource_name": datasource.value}],
        )
        flags = list(self.filter_flags(flags, datasource))
        num_flags = len(flags)
        for i, (flag, flag_ref) in enumerate(flags):
            logger.info(f"processing flag {i + 1}/{num_flags} :: {flag.pk} - {flag}")

            # find traineras.es MIX races
            race_refs = list(self.client.get_race_ids_by_flag(flag_ref))
            if len(race_refs) < 1:
                continue

            # filter races with given race_refs
            races = Race.objects.prefetch_related("participants").filter(
                flag=flag,
                metadata__datasource__contains=[{"datasource_name": datasource.value}],
            )
            races = list(self.filter_races(races, datasource, race_refs))
            num_races = len(races)
            for j, (db_race, ref_id) in enumerate(races):
                logger.info(f"processing race {j + 1}/{num_races} :: {db_race.pk} - {db_race}")
                race = self.client.get_race_by_id(ref_id)
                # ensure parsed data is what we expect
                if not race:
                    logger.error(f"no race found for {ref_id=}")
                    continue
                if race.gender != GENDER_MIX:
                    logger.error("found race is not a MIX race")
                    continue

                # get mix participants (every participant should be a mix participant)
                participants = [p for p in race.participants if p.gender == GENDER_MIX]
                race.participants = []
                if len(participants) < 1:
                    logger.error("no mix participants found")
                    continue

                ds = db_race.get_datasources(datasource, ref_id)
                assert len(ds) == 1, "more than one datasource found"

                ds = ds[0]
                race_d = race.to_dict()
                race_d.pop("participants")
                race_d = clean_dict(race_d)
                ds["data"] = race_d
                ds["date"] = datetime.now().date().isoformat()
                logger.info("updating race metadata")

                to_update = []
                for participant in participants:
                    match = self.find_participant(participant, list(db_race.participants.all()))

                    if not match:
                        logger.error(f"no match found for {participant=}")
                        continue

                    match.gender = GENDER_MIX
                    match.category = CATEGORY_ABSOLUT

                    ds_p = match.get_datasources(datasource)
                    assert len(ds_p) == 1, "more than one datasource found"

                    ds_p = ds_p[0]
                    participant_d = participant.to_dict()
                    participant_d.pop("penalty", None)
                    participant_d.pop("race", None)
                    participant_d = clean_dict(participant_d)
                    ds_p["data"] = participant_d
                    ds_p["date"] = datetime.now().date().isoformat()
                    logger.info("updating participant metadata")

                    to_update.append(match)

                assert len(to_update) > 0, "no participants to update"

                logger.info(f"updating {len(to_update)} participants")
                Participant.objects.bulk_update(to_update, ["metadata", "gender", "category"])
                logger.info(f"updating {db_race=}")
                db_race.save()

                time.sleep(5)
            time.sleep(5)

    def find_participant(self, participant: RSParticipant, db_participants: list[Participant]) -> Participant | None:
        if len(participant.laps) < 1:
            return

        for p in db_participants:
            if len(p.laps) < 1:
                continue
            if (
                p.category == CATEGORY_SCHOOL
                and p.laps[-1] == datetime.strptime(participant.laps[-1], "%M:%S.%f").time()
            ):
                return p

        for p in db_participants:
            if len(p.laps) < 1:
                continue
            if p.laps[-1] == datetime.strptime(participant.laps[-1], "%M:%S.%f").time():
                return p
