import json
import logging
from datetime import datetime
from typing import override

from django.core.exceptions import ValidationError

from apps.actions.management.helpers.input import (
    input_associated,
    input_club,
    input_competition,
    input_new_value,
    input_should_add_datasource,
    input_should_associate_races,
    input_should_merge,
    input_should_merge_participant,
    input_should_reset_league,
    input_should_save,
    input_should_save_participant,
    input_should_save_second_day,
)
from apps.actions.management.helpers.retrieval import (
    retrieve_competition,
    retrieve_database_race,
    retrieve_entity,
    retrieve_league,
)
from apps.actions.serializers import ParticipantSerializer, RaceSerializer
from apps.entities.models import Entity, League
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.places.models import Place
from apps.places.services import PlacesService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, RaceService, TrophyService
from apps.schemas import MetadataBuilder
from pyutils.shortcuts import clean_dict
from rscraping.clients import ClientProtocol
from rscraping.data.checks import is_branch_club
from rscraping.data.constants import CATEGORY_ALL, GENDER_ALL, RACE_TIME_TRIAL
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Penalty as RSPenalty
from rscraping.data.models import Race as RSRace

from ._protocol import DigesterProtocol

logger = logging.getLogger(__name__)


class Digester(DigesterProtocol):
    def __init__(
        self,
        client: ClientProtocol,
        force_gender: bool = False,
        force_category: bool = False,
        save_old: bool = False,
    ) -> None:
        self.client = client
        self._force_gender = force_gender
        self._force_category = force_category
        self._save_old = save_old

    @override
    def ingest(
        self,
        race: RSRace,
        hint: tuple[Flag, Trophy] | None = None,
        **kwargs,
    ) -> tuple[Race, Race | None, DigesterProtocol.Status]:
        logger.info(f"ingesting {race=}")
        logger.debug("searching race in the database")
        db_race = retrieve_database_race(
            race=race,
            hint=hint,
            force_gender=self._force_gender,
            force_category=self._force_category,
        )
        logger.info(f"using {db_race=}")

        logger.debug("searching league")
        league = retrieve_league(race, db_race)
        logger.info(f"using {league=}")

        db_race, (trophy, trophy_edition), (flag, flag_edition) = self._retrieve_competition(race, db_race, hint)
        assert (trophy and trophy_edition) or (flag and flag_edition), "missing competition data"
        logger.info(f"using {trophy=}:{trophy_edition=}")
        logger.info(f"using {flag=}:{flag_edition=}")

        logger.debug("searching organizer & town")
        place, organizer = self._update_race_with_competition_info(
            trophy,
            flag,
            league,
            race.town,
            race.organizer,
        )
        logger.info(f"using {organizer=} {place=}")

        new_race = Race(
            laps=race.race_laps,
            lanes=race.race_lanes,
            type=race.type,
            date=datetime.strptime(race.date, "%d/%m/%Y").date(),
            day=race.day,
            cancelled=race.cancelled,
            cancellation_reasons=[],
            race_names=[race.name],
            trophy=trophy,
            trophy_edition=trophy_edition,
            flag=flag,
            flag_edition=flag_edition,
            league=league,
            modality=race.modality,
            gender=race.gender,
            category=race.category,
            organizer=organizer,
            sponsor=race.sponsor,
            metadata=self._build_metadata(race, self.client.DATASOURCE),
            place=place,
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
        if len(db_race.get_datasources(self.client.DATASOURCE, datasource["ref_id"])) == 0:
            logger.debug("updating datasource")
            db_race.add_metadata(datasource)

        if db_race.gender != GENDER_ALL and db_race.gender != race.gender:
            logger.debug("setting gender=ALL")
            db_race.gender = GENDER_ALL

        if race.race_names:
            logger.debug("adding race_name")
            db_race.race_names = list(set(race.race_names + db_race.race_names))

        if db_race.category != CATEGORY_ALL and db_race.category != race.category:
            logger.debug("setting category=ALL")
            db_race.category = CATEGORY_ALL

        if not (db_race.laps == 4 and race.laps == 2) and input_new_value("laps", race.laps, db_race.laps):
            logger.debug(f"updating {db_race.laps} with {race.laps}")
            db_race.laps = race.laps

        if input_new_value("lanes", race.lanes, db_race.lanes):
            logger.debug(f"updating {db_race.lanes} with {race.lanes}")
            db_race.lanes = race.lanes

        if input_new_value("sponsor", race.sponsor, db_race.sponsor):
            logger.debug(f"updating {db_race.sponsor} with {race.sponsor}")
            db_race.sponsor = race.sponsor

        if input_new_value("place", race.place, db_race.place):
            logger.debug(f"updating {db_race.place} with {race.place}")
            db_race.place = race.place

        return db_race, DigesterProtocol.Status.MERGED

    @override
    def save(
        self,
        race: Race,
        status: DigesterProtocol.Status,
        associated: Race | None = None,
        **_,
    ) -> tuple[Race, DigesterProtocol.Status]:
        save_old_races = self._save_old and race.date.year < 2003

        if not save_old_races and not input_should_save(race):
            logger.warning(f"race {race} was not saved")
            return race, status

        if race.day == 2 and not associated and not race.associated:
            logger.debug("associated race not found")
            associated = input_associated(race)

        if associated and not race.associated and (save_old_races or input_should_associate_races(race, associated)):
            logger.info(f"associating races {race} and {associated}")
            race.associated = associated
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
        can_be_branch: bool,
        **_,
    ) -> tuple[Participant, DigesterProtocol.Status]:
        logger.info(f"ingesting {participant=}")

        logger.debug("searching entity in the database")
        club = retrieve_entity(participant.participant)
        if not club:
            club = input_club(participant.participant)
        assert club, "missing club data"
        logger.info(f"using {club=}")

        branch = None
        if is_branch_club(participant.participant):
            logger.info("'B' club detected")
            branch = "B"
        if is_branch_club(participant.participant, letter="C"):
            logger.info("'C' club detected")
            branch = "C"
        if is_branch_club(participant.participant, letter="D"):
            logger.info("'D' club detected")
            branch = "D"

        logger.debug("searching participant in the database")
        db_participant = ParticipantService.get_by_race_and_filter_by(
            race,
            club=club,
            gender=participant.gender,
            category=participant.category,
            branch=branch,
            raw_club_name=participant.club_name,
        )
        logger.info(f"using {db_participant=}")

        new_participant = Participant(
            club_names=[participant.club_name.upper().replace(".", "").strip()] if participant.club_name else [],
            club=club,
            branch=branch if can_be_branch else None,
            race=race,
            distance=participant.distance,
            laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in participant.laps],
            lane=participant.lane if race.type != RACE_TIME_TRIAL else 1,
            series=participant.series,
            handicap=datetime.strptime(participant.handicap, "%M:%S.%f").time() if participant.handicap else None,
            gender=participant.gender,
            category=participant.category,
            absent=participant.absent,
            retired=participant.retired and (not participant.penalty or not participant.penalty.disqualification),
            metadata=self._build_participant_metadata(participant, self.client.DATASOURCE),
        )

        status = DigesterProtocol.Status.NEW
        if db_participant:
            new_participant.club_names = list(set(new_participant.club_names + db_participant.club_names))
            fields = self.get_participant_fields_to_update(new_participant, db_participant)
            if len(fields) > 0 and fields != ["metadata"]:
                serialized = ParticipantSerializer(new_participant).data
                print(f"NEW PARTICIPANT:\n{json.dumps(serialized, indent=4, skipkeys=True, ensure_ascii=False)}")
                new_participant, status = self.merge_participants(new_participant, db_participant, status)
            else:
                # do metadata update transparently
                if fields == ["metadata"]:
                    logger.debug("updating metadata")
                    db_participant.add_metadata(new_participant.metadata["datasource"][0])
                    db_participant.club_names = list(set(new_participant.club_names + db_participant.club_names))
                    db_participant.save()
                serialized = ParticipantSerializer(db_participant).data
                print(f"EXISTING PARTICIPANT:\n{json.dumps(serialized, indent=4, skipkeys=True, ensure_ascii=False)}")
                return db_participant, DigesterProtocol.Status.EXISTING

        return new_participant, status

    @override
    def get_participant_fields_to_update(self, participant: Participant, db_participant: Participant) -> list[str]:
        fields = []

        if len(participant.laps) > len(db_participant.laps):
            fields.append("laps")
        if participant.lane is not None and participant.lane != db_participant.lane:
            fields.append("lane")
        if participant.metadata["datasource"][0] not in db_participant.metadata["datasource"]:
            fields.append("metadata")

        return fields

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
            has_datasource = len(db_participant.get_datasources(self.client.DATASOURCE)) > 0
            if not has_datasource and input_should_add_datasource(db_participant):
                logger.debug("adding new datasource")
                db_participant.add_metadata(participant.metadata["datasource"][0])
                db_participant.club_names = list(set(participant.club_names + db_participant.club_names))
                return db_participant, DigesterProtocol.Status.MERGED
            return participant, status

        fields = self.get_participant_fields_to_update(participant, db_participant)
        logger.info(f"merging {participant=} and {db_participant=}")

        if "metadata" in fields:
            logger.debug("updating datasource")
            db_participant.add_metadata(participant.metadata["datasource"][0])
            db_participant.club_names = list(set(participant.club_names + db_participant.club_names))

        if "laps" in fields and input_new_value("laps", participant.laps, db_participant.laps):
            logger.debug(f"updating {db_participant.laps} with {participant.laps}")
            db_participant.laps = participant.laps

        if "lane" in fields and input_new_value("lane", participant.lane, db_participant.lane):
            logger.debug(f"updating {db_participant.lane=} with {participant.lane=}")
            db_participant.lane = participant.lane

        return db_participant, DigesterProtocol.Status.MERGED

    @override
    def save_participant(
        self,
        participant: Participant,
        race_status: DigesterProtocol.Status,
        participant_status: DigesterProtocol.Status,
        **_,
    ) -> tuple[Participant, DigesterProtocol.Status]:
        if race_status != DigesterProtocol.Status.CREATED and not input_should_save_participant(participant):
            logger.warning(f"participant {participant} was not saved")
            return participant, participant_status

        logger.info(f"saving {participant=}")
        participant.save()
        return participant, participant_status.next()

    @override
    def save_penalty(self, participant: Participant, penalty: RSPenalty, note: str | None, **_) -> Penalty:
        logger.info(f"saving {penalty=} for {participant}")
        penalties = ParticipantService.get_penalties(participant)

        if penalties.count() > 1:
            logger.warning(f"multiple penalties found for {participant=}")
            penalties = penalties.filter(reason__isnull=False, reason=penalty.reason)

        if penalties.count() == 1:
            db_penalty = penalties.first()
            assert db_penalty, "missing penalty data"

            if not db_penalty.reason or penalty.reason == db_penalty.reason:
                db_penalty.reason = db_penalty.reason if db_penalty.reason else penalty.reason
                if note and note not in db_penalty.notes:
                    db_penalty.notes.append(note)
                db_penalty.save()
                return db_penalty

        new_penalty = Penalty(
            reason=penalty.reason,
            disqualification=penalty.disqualification,
            participant=participant,
            notes=[note] if note else [],
        )
        new_penalty.save()
        return new_penalty

    @override
    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict:
        if not race.url:
            raise ValueError(f"no datasource provided for {race.race_ids[0]}::{race.name}")

        race_d = race.to_dict()
        race_d.pop("participants", None)
        race_d = clean_dict(race_d)

        return {
            "datasource": [
                MetadataBuilder()
                .ref_id(race_id)
                .datasource_name(datasource)
                .values("details_page", race.url)
                .data(race_d)
                .build()
                for race_id in race.race_ids
            ]
        }

    @override
    def _build_participant_metadata(self, participant: RSParticipant, datasource: Datasource) -> dict:
        participant_d = participant.to_dict()
        participant_d.pop("penalty", None)
        participant_d.pop("race", None)
        participant_d = clean_dict(participant_d)

        return {"datasource": [MetadataBuilder().datasource_name(datasource).data(participant_d).build()]}

    def _update_race_with_competition_info(
        self,
        trophy: Trophy | None,
        flag: Flag | None,
        league: League | None,
        town: str | None,
        organizer_name: str | None,
    ) -> tuple[Place | None, Entity | None]:
        place = PlacesService.get_closest_by_name_or_none(town) if town else None
        organizer = retrieve_entity(organizer_name, entity_type=None) if organizer_name else None
        competitions = RaceService.get_races_by_competition(trophy, flag, league)
        if competitions.count():
            logger.debug(f"found {competitions.count()} matching races")
            if not place:
                places = Place.objects.filter(
                    id__in=competitions.select_related("place")
                    .filter(place__isnull=False)
                    .values_list("place", flat=True)
                    .distinct()
                )
                if places.count() == 1:
                    logger.info(f"updating {places.first()=}")
                    place = places.first()

            if not organizer:
                organizers = Entity.all_objects.filter(
                    id__in=competitions.filter(organizer__isnull=False).values_list("organizer", flat=True).distinct()
                )
                if organizers.count() == 1:
                    logger.info(f"updating {organizer=} with {organizers.first()}")
                    organizer = organizers.first()
        return place, organizer

    @staticmethod
    def _retrieve_competition(
        race: RSRace,
        db_race: Race | None,
        hint: tuple[Flag, Trophy] | None,
    ) -> tuple[Race | None, tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
        logger.debug("searching trophy")
        trophy, trophy_edition = retrieve_competition(
            Trophy,
            race,
            db_race,
            TrophyService.get_closest_by_name_or_none,
            TrophyService.infer_trophy_edition,
            hint[1] if hint else None,
        )

        logger.debug("searching flag")
        flag, flag_edition = retrieve_competition(
            Flag,
            race,
            db_race,
            FlagService.get_closest_by_name_or_none,
            FlagService.infer_flag_edition,
            hint[0] if hint else None,
        )
        return (db_race, (trophy, trophy_edition), (flag, flag_edition)) if trophy or flag else input_competition(race)
