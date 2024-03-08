import json
import logging
import time
from collections.abc import Generator
from datetime import date, datetime
from typing import Any, override

from django.core.exceptions import ValidationError
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.input import (
    input_club,
    input_competition,
    input_should_associate_races,
    input_should_merge,
    input_should_merge_participant,
    input_should_save,
    input_should_save_participant,
    input_should_save_second_day,
    input_update_value,
)
from apps.actions.management.helpers.retrieval import retrieve_competition, retrieve_entity, retrieve_league
from apps.actions.serializers import ParticipantSerializer, RaceSerializer
from apps.entities.normalization import normalize_club_name
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, MetadataService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from rscraping import Datasource
from rscraping.clients import ClientProtocol
from rscraping.data.constants import GENDER_ALL
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace

from ._protocol import IngestorProtocol

logger = logging.getLogger(__name__)


class Ingestor(IngestorProtocol):
    def __init__(self, client: ClientProtocol, ignored_races: list[str]):
        self.client = client
        self._ignored_races = ignored_races

    @staticmethod
    def _is_race_after_today(race: RSRace) -> bool:
        return datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()

    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_race_ids_by_year(year=year):
            if race_id in self._ignored_races or MetadataService.exists(race_id, self.client.DATASOURCE):
                logger.info(f"ignoring {race_id=}")
                continue

            try:
                time.sleep(1)
                race = self.client.get_race_by_id(race_id)
                if not race:
                    continue
                if self._is_race_after_today(race):
                    break
                logger.info(f"found race for {race_id=}:\n\t{race}")
                yield race

            except ValueError as e:
                logger.error(e)
                continue

    @override
    def fetch_by_ids(self, race_ids: list[str], day: int | None = None, **_) -> Generator[RSRace, Any, Any]:
        for race_id in race_ids:
            race = self.client.get_race_by_id(race_id, day=day)
            if race:
                logger.info(f"found race for {race_id=}:\n\t{race}")
                yield race
            time.sleep(1)

    @override
    def ingest(self, race: RSRace, **kwargs) -> tuple[Race, Race | None]:
        logger.info(f"ingesting {race=}")

        metadata = self._validate_datasource_and_build_metadata(race, self.client.DATASOURCE)

        logger.info("searching race in the database")
        db_race = RaceService.get_closest_match_by_name_or_none(
            names=[n for n, _ in race.normalized_names],
            league=race.league,
            gender=race.gender,
            date=datetime.strptime(race.date, "%d/%m/%Y").date(),
            day=race.day,
        )
        logger.info(f"found {db_race=}")

        logger.info("searching league")
        league = retrieve_league(race, db_race)
        logger.info(f"using {league=}")

        db_race, (trophy, trophy_edition), (flag, flag_edition) = self._retrieve_competition(race, db_race=db_race)
        if (not trophy and not flag) or (trophy and not trophy_edition) or (flag and not flag_edition):
            raise StopProcessing("missing competition data")
        logger.info(f"using {trophy=}:{trophy_edition=}")
        logger.info(f"using {flag=}:{flag_edition=}")

        logger.info("searching organizer")
        organizer = retrieve_entity(normalize_club_name(race.organizer), entity_type=None) if race.organizer else None
        logger.info(f"using {organizer=}")

        new_race = Race(
            laps=race.race_laps,
            lanes=race.race_lanes,
            town=race.town,
            type=race.type,
            date=datetime.strptime(race.date, "%d/%m/%Y").date(),
            day=race.day,
            cancelled=race.cancelled,
            cancellation_reasons=[],
            race_name=race.name,
            trophy=trophy,
            trophy_edition=trophy_edition,
            flag=flag,
            flag_edition=flag_edition,
            league=league,
            modality=race.modality,
            gender=race.gender,
            organizer=organizer,
            sponsor=race.sponsor,
            metadata=metadata,
        )

        logger.info("searching analogous race")
        associated = RaceService.get_analogous_or_none(
            race=new_race,
            year=datetime.strptime(race.date, "%d/%m/%Y").date().year,
            day=2 if race.day == 1 else 1,
        )
        logger.info(f"using {associated=}")

        if not db_race:
            logger.info("searching race in the database")
            db_race = RaceService.get_by_race(new_race)
            logger.info(f"using {db_race=}")

        print(f"NEW RACE:\n{json.dumps(RaceSerializer(new_race).data, indent=4, skipkeys=True, ensure_ascii=False)}")
        if db_race:
            new_race, _ = self.merge(new_race, db_race=db_race)

        return new_race, associated

    @override
    def merge(self, race: Race, db_race: Race) -> tuple[Race, bool]:
        serialized_race = RaceSerializer(db_race).data
        print(f"DATABASE RACE:\n{json.dumps(serialized_race, indent=4, skipkeys=True, ensure_ascii=False)}")
        if not input_should_merge(db_race):
            logger.info(f"races will not be merged, using {race=}")
            return race, False

        logger.info(f"merging {race=} and {db_race=}")
        datasource = race.metadata["datasource"][0]
        has_datasource = any(
            d["ref_id"] == datasource["ref_id"] and d["datasource_name"] == datasource["datasource_name"]
            for d in db_race.metadata["datasource"]
        )
        if not has_datasource:
            logger.info(f"adding {datasource}")
            db_race.metadata["datasource"].append(datasource)

        if db_race.gender != GENDER_ALL and db_race.gender != race.gender:
            logger.info("setting gender=ALL")
            db_race.gender = GENDER_ALL

        if race.laps and db_race.laps != race.laps and input_update_value("laps", race.laps, db_race.laps):
            logger.info(f"updating {db_race.laps} with {race.laps}")
            db_race.laps = race.laps

        if race.lanes and db_race.lanes != race.lanes and input_update_value("lanes", race.lanes, db_race.lanes):
            logger.info(f"updating {db_race.lanes} with {race.lanes}")
            db_race.lanes = race.lanes
        return db_race, True

    @override
    def save(self, race: Race, associated: Race | None = None, **_) -> tuple[Race, bool]:
        if not input_should_save(race):
            logger.info(f"race {race} was not saved")
            return race, False

        if associated and not race.associated and input_should_associate_races(race, associated):
            logger.info(f"associating races {race} and {associated}")
            race.associated = associated  # pyright: ignore
            race.save()
            Race.objects.filter(pk=associated.pk).update(associated=race)
            return race, True

        try:
            logger.info(f"race {race} was saved")
            race.save()
            return race, True
        except ValidationError:
            if race.day == 1 and input_should_save_second_day(race):
                logger.info(f"change day for {race} and trying again")
                race.day = 2
                return self.save(race, associated)
            return race, False

    @override
    def ingest_participant(
        self,
        race: Race,
        participant: RSParticipant,
        **_,
    ) -> Participant:
        logger.info(f"ingesting {participant=}")

        logger.info("searching entity in the database")
        club = retrieve_entity(normalize_club_name(participant.participant))
        if not club:
            club = input_club(participant.participant)
        if not club:
            raise StopProcessing("missing club data")
        logger.info(f"using {club=}")

        logger.info("searching participant in the database")
        db_participant = ParticipantService.get_by_race_and_filter_by(
            race,
            club=club,
            category=participant.category,
            gender=participant.gender,
            raw_club_name=participant.club_name,
        )
        logger.info(f"found {db_participant=}")

        new_participant = Participant(
            club_name=participant.club_name,
            club=club,
            race=race,
            distance=participant.distance,
            laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in participant.laps],
            lane=participant.lane,
            series=participant.series,
            handicap=datetime.strptime(participant.handicap, "%M:%S.%f").time() if participant.handicap else None,
            gender=participant.gender,
            category=participant.category,
        )

        serialized_participant = ParticipantSerializer(new_participant).data
        print(f"NEW PARTICIPANT:\n{json.dumps(serialized_participant, indent=4, skipkeys=True, ensure_ascii=False)}")

        if db_participant:
            new_participant, _ = self.merge_participants(new_participant, db_participant)

        return new_participant

    @override
    def merge_participants(self, participant: Participant, db_participant: Participant) -> tuple[Participant, bool]:
        serialized_participant = ParticipantSerializer(db_participant).data
        json_participant = json.dumps(serialized_participant, indent=4, skipkeys=True, ensure_ascii=False)
        print(f"DATABASE PARTICIPANT:\n{json_participant}")
        if not input_should_merge_participant(db_participant):
            logger.info(f"participants will not be merged, using {participant=}")
            return participant, False
        return db_participant, True

    @override
    def save_participant(
        self,
        participant: Participant,
        is_disqualified: bool = False,
        **_,
    ) -> tuple[Participant, bool]:
        if not input_should_save_participant(participant):
            logger.info(f"participant {participant} was not saved")
            return participant, False

        logger.info(f"participant {participant} was saved")
        participant.save()
        if is_disqualified:
            logger.info(f"creating disqualification penalty for {participant}")
            Penalty(disqualification=True, participant=participant).save()
        return participant, True

    @override
    @staticmethod
    def _validate_datasource_and_build_metadata(race: RSRace, datasource: Datasource) -> dict:
        if not race.url:
            raise ValueError(f"no datasource provided for {race.race_ids[0]}::{race.name}")

        return {
            "datasource": [
                MetadataBuilder().ref_id(race_id).datasource_name(datasource).values("details_page", race.url).build()
                for race_id in race.race_ids
            ]
        }

    @staticmethod
    def _retrieve_competition(
        race: RSRace,
        db_race: Race | None,
    ) -> tuple[Race | None, tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
        logger.info("searching trophy")
        trophy, trophy_edition = retrieve_competition(
            Trophy,
            race,
            db_race,
            TrophyService.get_closest_by_name_or_none,
            TrophyService.infer_trophy_edition,
        )

        logger.info("searching flag")
        flag, flag_edition = retrieve_competition(
            Flag,
            race,
            db_race,
            FlagService.get_closest_by_name_or_none,
            FlagService.infer_flag_edition,
        )

        if not trophy and not flag:
            logger.info("no trophy or flag found, asking user for input")
            db_race, (trophy, trophy_edition), (flag, flag_edition) = input_competition(race)

        return db_race, (trophy, trophy_edition), (flag, flag_edition)
