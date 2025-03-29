#!/usr/bin/env python3

import logging
import time
from collections.abc import Generator
from datetime import datetime

import inquirer
from django.core.management import BaseCommand
from django.db.models import Q, QuerySet

from apps.actions.management.digester._digester import Digester
from apps.entities.services import EntityService
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Race
from apps.schemas import MetadataBuilder
from pyutils.dicts import clean_dict
from rscraping.clients import Client, TrainerasClient
from rscraping.data.checks import is_branch_club
from rscraping.data.constants import CATEGORY_ABSOLUT, CATEGORY_VETERAN, GENDER_FEMALE, GENDER_MALE
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("fixes4.log")
formatter = logging.Formatter("%(levelname)s %(asctime)s %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Command(BaseCommand):
    m_abs_client = TrainerasClient(source=Datasource.TRAINERAS, gender=GENDER_MALE, category=CATEGORY_ABSOLUT)
    m_abs_digester = Digester(m_abs_client, force_gender=True, force_category=True)
    f_abs_client = TrainerasClient(source=Datasource.TRAINERAS, gender=GENDER_FEMALE, category=CATEGORY_ABSOLUT)
    f_abs_digester = Digester(f_abs_client, force_gender=True, force_category=True)
    m_vet_client = TrainerasClient(source=Datasource.TRAINERAS, gender=GENDER_MALE, category=CATEGORY_VETERAN)
    m_vet_digester = Digester(m_vet_client, force_gender=True, force_category=True)
    f_vet_client = TrainerasClient(source=Datasource.TRAINERAS, gender=GENDER_FEMALE, category=CATEGORY_VETERAN)
    f_vet_digester = Digester(f_vet_client, force_gender=True, force_category=True)

    def client(self, race: Race) -> Client:
        if race.gender == GENDER_FEMALE:
            return self.f_abs_client if race.category == CATEGORY_ABSOLUT else self.f_vet_client
        else:
            return self.m_abs_client if race.category == CATEGORY_ABSOLUT else self.m_vet_client

    def digester(self, race: Race) -> Digester:
        if race.gender == GENDER_FEMALE:
            return self.f_abs_digester if race.category == CATEGORY_ABSOLUT else self.f_vet_digester
        else:
            return self.m_abs_digester if race.category == CATEGORY_ABSOLUT else self.m_vet_digester

    def filter_races(self, races: QuerySet[Race], datasource: Datasource) -> Generator[tuple[Race, str]]:
        for race in races:
            if all(len(p.metadata["datasource"]) > 0 or p.absent or p.retired for p in race.participants.all()):
                continue
            for ds in race.metadata["datasource"]:
                if ds["datasource_name"] == datasource.value:
                    yield (race, ds["ref_id"])

    def handle(self, *_, **options):
        logger.info(f"{options}")

        datasource = Datasource.TRAINERAS.value
        races = Race.objects.prefetch_related("participants", "participants__penalties").filter(
            Q(metadata__datasource__contains=[{"datasource_name": datasource}])
            # & ~Q(metadata__datasource__has_key="data"),
        )

        races = list(self.filter_races(races, Datasource.TRAINERAS))
        num_races = len(races)
        for i, (db_race, ref_id) in enumerate(races):
            logger.info(f"processing race {i + 1}/{num_races} :: {db_race.pk} - {db_race}")
            client, digester = self.client(db_race), self.digester(db_race)

            if db_race.trophy and db_race.trophy.pk == 24:
                # HACK: fix Teresa Herrera being saved as 3 tables
                logger.info("processing Teresa Herrera Final")
                race = client.get_race_by_id(ref_id, table=3)
                if not race:
                    race = client.get_race_by_id(ref_id, table=2)
                if not race:
                    race = client.get_race_by_id(ref_id, table=1)
            elif db_race.trophy and db_race.trophy.pk == 25:
                # HACK: fix Teresa Herrera cassification
                if client.get_race_by_id(ref_id, table=3) is not None:
                    race_1 = client.get_race_by_id(ref_id, table=1)
                    race_2 = client.get_race_by_id(ref_id, table=2)
                    assert race_1 is not None, "error loading table 1"
                    assert race_2 is not None, "error loading table 2"
                    participants = race_1.participants + race_2.participants
                    race = race_1
                    race.participants = participants
                else:
                    race = client.get_race_by_id(ref_id, table=1)
            else:
                race = client.get_race_by_id(ref_id, table=db_race.day)
                if not race and db_race.day == 2:
                    race = client.get_race_by_id(ref_id, table=1)

            if not race:
                logger.error(f"no race found for {ref_id=}")
                continue

            participants = race.participants
            race.participants = []

            # 1. UPDATE RACE METADATA
            logger.info("updating race metadata")
            metadata = db_race.metadata["datasource"]
            ds = [d for d in metadata if d["datasource_name"] == datasource and d["ref_id"] == ref_id][0]
            race_d = race.to_dict()
            race_d.pop("participants")
            race_d = clean_dict(race_d)
            ds["data"] = race_d
            ds["date"] = datetime.now().date().isoformat()

            # 2. PRELOAD PARTICIPANT CLUBS
            logger.info("preloading participant clubs")
            clubs = [(p, EntityService.get_closest_club_by_name(p.participant)) for p in participants]

            db_participants = list(db_race.participants.filter(gender=race.gender, category=race.category))
            for db_participant in db_participants:
                if len(db_participant.metadata["datasource"]) > 0:
                    continue
                # 3. MATCH PARTICIPANTS
                logger.info(f"processing {db_participant=}")
                participant = next(
                    (p for p, c in clubs if ParticipantService.is_same_participant(db_participant, p, c)),
                    None,
                )

                # 3.1. ASK FOR PARTICIPANT IF UNABLE TO MATCH
                if not participant and not (db_participant.absent or db_participant.retired or db_race.cancelled):
                    participant_names = [p.participant for p in participants] + ["SKIP"]
                    participant = inquirer.list_input(f"participant={db_participant}", choices=participant_names)
                    if participant == "SKIP":
                        continue
                    participant = next((p for p in participants if p.participant == participant), None)

                if not participant and (
                    db_participant.retired
                    or db_participant.absent
                    or len(db_participant.laps) == 0
                    or db_race.cancelled
                ):
                    logger.warning(f"skipping {db_participant=}")
                    continue

                assert participant is not None, "participant not found"
                assert len(db_participant.metadata["datasource"]) == 0, "metadata should be empty"

                # 4. UPDATE PARTICIPANT METADATA
                logger.info("updating participant metadata")
                participant_d = participant.to_dict()
                participant_d.pop("penalty", None)
                participant_d.pop("race", None)
                participant_d = clean_dict(participant_d)
                db_participant.metadata["datasource"] = [
                    MetadataBuilder().datasource_name(Datasource.TRAINERAS).data(participant_d).build()
                ]

                # 5. UPDATE PARTICIPANT BRANCH
                logger.info("updating participant branch")
                if is_branch_club(participant.participant):
                    db_participant.branch = "B"
                if is_branch_club(participant.participant, letter="C"):
                    db_participant.branch = "C"
                if is_branch_club(participant.participant, letter="D"):
                    db_participant.branch = "D"

                # 6. UPDATE PENALTIES
                if participant.penalty:
                    logger.info("creating penalty")
                    _ = digester.save_penalty(db_participant, participant.penalty, race.race_notes)

                participants = [p for p in participants if p != participant]
                clubs = [(p, c) for p, c in clubs if p != participant]

            # 7. DIGEST NEW PARTICIPANTS
            if len(participants) > 0:
                logger.warning(f"missing {participants=} in {db_race}")
                for participant in participants:
                    logger.info(f"digesting new {participant=}")
                    can_be_branch_team = db_race.league is None and ParticipantService.can_be_branch(
                        participant.participant,
                        [p.participant for p in participants],
                    )
                    new_participant, status = digester.ingest_participant(
                        db_race,
                        participant,
                        can_be_branch=can_be_branch_team,
                    )
                    if status == Digester.Status.NEW or status == Digester.Status.MERGED:
                        new_participant, status = digester.save_participant(
                            new_participant,
                            race_status=Digester.Status.NEW,
                            participant_status=status,
                        )
                    if new_participant.pk and participant.penalty:
                        _ = digester.save_penalty(new_participant, participant.penalty, race.race_notes)

            # 8. UPDATE PENALTIES (AGAIN)
            if race.race_notes:
                logger.info("digesting penalties")
                penalties = Penalty.objects.filter(participant__in=db_participants)
                for penalty in penalties:
                    if race.race_notes not in penalty.notes:
                        penalty.notes.append(race.race_notes)

                logger.info("bulk updating penalties")
                Penalty.objects.bulk_update(penalties, ["notes"])

            logger.info("bulk updating participants")
            Participant.objects.bulk_update(db_participants, ["metadata", "branch"])
            # logger.info(f"saving race={db_race.pk}")
            # db_race.save()

            if race.race_notes:
                logger.warning(f"NOTES: {race.race_notes}")

            time.sleep(5)
            if (i + 1) % 50 == 0:
                logger.info("sleeping longer")
                time.sleep(60)
