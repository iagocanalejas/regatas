import json
import logging
from datetime import datetime
from typing import override

from django.core.exceptions import ValidationError
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.input import (
    input_club,
    input_competition,
    input_new_value,
    input_race,
    input_should_associate_races,
    input_should_merge,
    input_should_merge_participant,
    input_should_reset_league,
    input_should_save,
    input_should_save_participant,
    input_should_save_second_day,
)
from apps.actions.management.helpers.retrieval import retrieve_competition, retrieve_entity, retrieve_league
from apps.actions.serializers import ParticipantSerializer, RaceSerializer
from apps.entities.models import Entity, League
from apps.entities.normalization import normalize_club_name
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, MetadataService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from rscraping.clients import ClientProtocol
from rscraping.data.constants import GENDER_ALL
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace

from ._protocol import DigesterProtocol

logger = logging.getLogger(__name__)


class Digester(DigesterProtocol):
    def __init__(self, client: ClientProtocol, force_gender: bool = False):
        self.client = client
        self._force_gender = force_gender

    @override
    def ingest(self, race: RSRace, **kwargs) -> tuple[Race, Race | None, DigesterProtocol.Status]:
        logger.info(f"ingesting {race=}")

        metadata = self._build_metadata(race, self.client.DATASOURCE)

        logger.debug("searching race in the database")
        try:
            db_race = RaceService.get_closest_match_by_name_or_none(
                names=[n for n, _ in race.normalized_names],
                league=race.league,
                gender=race.gender,
                date=datetime.strptime(race.date, "%d/%m/%Y").date(),
                day=race.day,
                force_gender=self._force_gender,
            )
        except Race.MultipleObjectsReturned:
            logger.error(f"multiple races found for {race.date}:{race.name}")
            db_race = input_race(race)
        logger.info(f"using {db_race=}")

        logger.debug("searching league")
        league = retrieve_league(race, db_race)
        logger.info(f"using {league=}")

        db_race, (trophy, trophy_edition), (flag, flag_edition) = self._retrieve_competition(race, db_race=db_race)
        if (not trophy and not flag) or (trophy and not trophy_edition) or (flag and not flag_edition):
            raise StopProcessing("missing competition data")
        logger.info(f"using {trophy=}:{trophy_edition=}")
        logger.info(f"using {flag=}:{flag_edition=}")

        logger.debug("searching organizer & town")
        town, organizer = self._update_race_with_competition_info(trophy, flag, league, race.town, race.organizer)
        logger.info(f"using {organizer=} {town=}")

        new_race = Race(
            laps=race.race_laps,
            lanes=race.race_lanes,
            town=town,
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

        logger.debug("searching analogous race")
        associated = RaceService.get_analogous_or_none(
            race=new_race,
            year=datetime.strptime(race.date, "%d/%m/%Y").date().year,
            day=2 if race.day == 1 else 1,
        )
        logger.info(f"using {associated=}")

        if not db_race:
            logger.debug("searching race in the database")
            db_race = RaceService.get_race_matching_race(new_race)
            logger.info(f"using {db_race=}")

        print(f"NEW RACE:\n{json.dumps(RaceSerializer(new_race).data, indent=4, skipkeys=True, ensure_ascii=False)}")
        status = DigesterProtocol.Status.NEW
        if db_race:
            new_race, status = self.merge(new_race, db_race=db_race, status=status)
        if status == DigesterProtocol.Status.NEW and db_race and not associated:
            # if we had a match but we didn't merge, it can be an associated race
            associated = db_race
            logger.info(f"using {associated=}")
        return new_race, associated, status

    @override
    def merge(self, race: Race, db_race: Race, status: DigesterProtocol.Status) -> tuple[Race, DigesterProtocol.Status]:
        serialized_race = RaceSerializer(db_race).data
        print(f"DATABASE RACE:\n{json.dumps(serialized_race, indent=4, skipkeys=True, ensure_ascii=False)}")
        if not input_should_merge(db_race):
            logger.debug(f"races will not be merged, using {race=}")
            if input_should_reset_league():
                race.league = None
            return race, status

        logger.info(f"merging {race=} and {db_race=}")
        datasource = race.metadata["datasource"][0]
        if not self._get_datasource(db_race, datasource["ref_id"]):
            logger.debug("updating datasource")
            db_race.metadata["datasource"].append(datasource)

        if db_race.gender != GENDER_ALL and db_race.gender != race.gender:
            logger.debug("setting gender=ALL")
            db_race.gender = GENDER_ALL

        if input_new_value("laps", race.laps, db_race.laps):
            logger.debug(f"updating {db_race.laps} with {race.laps}")
            db_race.laps = race.laps

        if input_new_value("lanes", race.lanes, db_race.lanes):
            logger.debug(f"updating {db_race.lanes} with {race.lanes}")
            db_race.lanes = race.lanes

        if input_new_value("sponsor", race.sponsor, db_race.sponsor):
            logger.debug(f"updating {db_race.sponsor} with {race.sponsor}")
            db_race.sponsor = race.sponsor

        if input_new_value("town", race.town, db_race.town):
            logger.debug(f"updating {db_race.town} with {race.town}")
            db_race.town = race.town

        return db_race, DigesterProtocol.Status.MERGED

    @override
    def save(
        self,
        race: Race,
        status: DigesterProtocol.Status,
        associated: Race | None = None,
        **_,
    ) -> tuple[Race, DigesterProtocol.Status]:
        if not input_should_save(race):
            logger.warning(f"race {race} was not saved")
            return race, status

        if associated and not race.associated and input_should_associate_races(race, associated):
            logger.info(f"associating races {race} and {associated}")
            race.associated = associated  # pyright: ignore
            race.save()
            Race.objects.filter(pk=associated.pk).update(associated=race)
            return race, status.next()

        try:
            logger.info(f"saving {race=}")
            race.save()
            return race, status.next()
        except ValidationError as e:
            logger.error(e)
            if race.day == 1 and input_should_save_second_day(race):
                logger.debug(f"change day for {race} and trying again")
                race.day = 2
                return self.save(race, status, associated)
            return race, status

    @override
    def ingest_participant(
        self,
        race: Race,
        participant: RSParticipant,
        **_,
    ) -> tuple[Participant, DigesterProtocol.Status]:
        logger.info(f"ingesting {participant=}")

        logger.debug("searching entity in the database")
        club = retrieve_entity(normalize_club_name(participant.participant))
        if not club:
            club = input_club(participant.participant)
        if not club:
            raise StopProcessing("missing club data")
        logger.info(f"using {club=}")

        logger.debug("searching participant in the database")
        db_participant = ParticipantService.get_by_race_and_filter_by(
            race,
            club=club,
            category=participant.category,
            gender=participant.gender,
            raw_club_name=participant.club_name,
        )
        logger.info(f"using {db_participant=}")

        new_participant = Participant(
            club_name=participant.club_name.upper() if participant.club_name else None,
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

        status = DigesterProtocol.Status.NEW
        if db_participant:
            if not self.should_merge_participants(new_participant, db_participant):
                serialized = ParticipantSerializer(db_participant).data
                print(f"EXISTING PARTICIPANT:\n{json.dumps(serialized, indent=4, skipkeys=True, ensure_ascii=False)}")
                return db_participant, DigesterProtocol.Status.EXISTING
            else:
                serialized = ParticipantSerializer(new_participant).data
                print(f"NEW PARTICIPANT:\n{json.dumps(serialized, indent=4, skipkeys=True, ensure_ascii=False)}")
                new_participant, status = self.merge_participants(new_participant, db_participant, status)

        return new_participant, status

    @override
    def should_merge_participants(self, participant: Participant, db_participant: Participant) -> bool:
        """
        Determines whether two participants should be merged based on certain conditions.

        Conditions for merging:
        1. If the number of laps for the first participant is greater than the number of laps for the second.
        2. If the lane of the first participant is not None and is different from the lane assigned to the second.
        3. If the second participant does not have a club name, but the first one has it
            and is different from the second participant's club name.
        """
        return (
            len(participant.laps) > len(db_participant.laps)
            or (participant.lane is not None and participant.lane != db_participant.lane)
            or (
                db_participant.club_name is None
                and participant.club_name is not None
                and participant.club_name != db_participant.club_name
            )
        )

    @override
    def merge_participants(
        self,
        participant: Participant,
        db_participant: Participant,
        status: DigesterProtocol.Status,
    ) -> tuple[Participant, DigesterProtocol.Status]:
        serialized_participant = ParticipantSerializer(db_participant).data
        json_participant = json.dumps(serialized_participant, indent=4, skipkeys=True, ensure_ascii=False)
        print(f"DATABASE PARTICIPANT:\n{json_participant}")
        if not input_should_merge_participant(db_participant):
            logger.warning(f"participants will not be merged, using {participant=}")
            return participant, status

        logger.info(f"merging {participant=} and {db_participant=}")
        if len(participant.laps) > len(db_participant.laps) and input_new_value(
            "laps", participant.laps, db_participant.laps
        ):
            logger.debug(f"updating {db_participant.laps} with {participant.laps}")
            db_participant.laps = participant.laps

        if input_new_value("lane", participant.lane, db_participant.lane):
            logger.debug(f"updating {db_participant.lane=} with {participant.lane=}")
            db_participant.lane = participant.lane

        if db_participant.club_name is None and input_new_value(
            "name", participant.club_name, db_participant.club_name
        ):
            logger.debug(f"updating {db_participant.club_name=} with {participant.club_name=}")
            db_participant.club_name = participant.club_name

        return db_participant, DigesterProtocol.Status.MERGED

    @override
    def save_participant(
        self,
        participant: Participant,
        race_status: DigesterProtocol.Status,
        participant_status: DigesterProtocol.Status,
        is_disqualified: bool = False,
        **_,
    ) -> tuple[Participant, DigesterProtocol.Status]:
        if race_status != DigesterProtocol.Status.CREATED and not input_should_save_participant(participant):
            logger.warning(f"participant {participant} was not saved")
            return participant, participant_status

        logger.info(f"saving {participant=}")
        participant.save()
        if is_disqualified:
            logger.info(f"creating disqualification penalty for {participant}")
            Penalty(disqualification=True, participant=participant).save()
        return participant, participant_status.next()

    @override
    def _get_datasource(self, race: Race, ref_id: str) -> dict | None:
        datasources = MetadataService.get_datasource_from_race(self.client.DATASOURCE, race, ref_id)
        if len(datasources) > 1:
            logger.warning(f"multiple datasources found for race {race=} and datasource {ref_id=}")
        return datasources[0] if datasources else None

    @override
    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict:
        if not race.url:
            raise ValueError(f"no datasource provided for {race.race_ids[0]}::{race.name}")

        return {
            "datasource": [
                MetadataBuilder().ref_id(race_id).datasource_name(datasource).values("details_page", race.url).build()
                for race_id in race.race_ids
            ]
        }

    def _update_race_with_competition_info(
        self,
        trophy: Trophy | None,
        flag: Flag | None,
        league: League | None,
        town: str | None,
        organizer_name: str | None,
    ) -> tuple[str | None, Entity | None]:
        organizer = retrieve_entity(normalize_club_name(organizer_name), entity_type=None) if organizer_name else None
        competitions = RaceService.get_races_by_competition(trophy, flag, league)
        if competitions.count():
            logger.debug(f"found {competitions.count()} matching races")
            towns = competitions.filter(town__isnull=False).values_list("town", flat=True).distinct()
            if not town and towns.count() == 1:
                logger.info(f"updating {town=} with {towns.first()}")
                town = towns.first()

            organizers = Entity.all_objects.filter(
                id__in=competitions.filter(organizer__isnull=False).values_list("organizer", flat=True).distinct()
            )
            if not organizer and organizers.count() == 1:
                logger.info(f"updating {organizer=} with {organizers.first()}")
                organizer = organizers.first()
        return town, organizer

    @staticmethod
    def _retrieve_competition(
        race: RSRace,
        db_race: Race | None,
    ) -> tuple[Race | None, tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
        logger.debug("searching trophy")
        trophy, trophy_edition = retrieve_competition(
            Trophy,
            race,
            db_race,
            TrophyService.get_closest_by_name_or_none,
            TrophyService.infer_trophy_edition,
        )

        logger.debug("searching flag")
        flag, flag_edition = retrieve_competition(
            Flag,
            race,
            db_race,
            FlagService.get_closest_by_name_or_none,
            FlagService.infer_flag_edition,
        )
        return (db_race, (trophy, trophy_edition), (flag, flag_edition)) if trophy or flag else input_competition(race)
