import logging
from collections.abc import Generator
from typing import Any, override

from apps.actions.management.helpers.input import input_new_value, input_shoud_create_B_participant
from apps.participants.models import Participant
from apps.races.models import Race
from apps.races.services import MetadataService
from apps.schemas import MetadataBuilder, default_metadata
from rscraping.clients import TabularDataClient
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace
from rscraping.data.normalization.leagues import normalize_league_name

from ._ingestor import Ingestor

logger = logging.getLogger(__name__)


class TabularIngestor(Ingestor):
    client: TabularDataClient

    def __init__(self, client: TabularDataClient, ignored_races: list[str]):
        self.client = client
        self._ignored_races = ignored_races

    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_race_ids_by_year(year=year):
            if race_id in self._ignored_races or MetadataService.exists(
                Datasource.TABULAR,
                race_id,
                sheet_id=self.client.config.sheet_id,
                sheet_name=self.client.config.sheet_name,
            ):
                continue

            race = self.client.get_race_by_id(race_id)
            if not race:
                continue
            logger.debug(f"found race for {race_id=}:\n\t{race}")

            is_female = race.gender == GENDER_FEMALE
            race.league = normalize_league_name(race.league, is_female=is_female) if race.league else None
            yield race

    @override
    def merge(self, race: Race, db_race: Race, status: Ingestor.Status) -> tuple[Race, Ingestor.Status]:
        db_race, status = super().merge(race, db_race, status)
        if status != Ingestor.Status.MERGED:
            return race, status

        if input_new_value("trophy_edition", race.trophy_edition, db_race.trophy_edition):
            logger.debug(f"updating {db_race.trophy_edition=} with {race.trophy_edition=}")
            db_race.trophy_edition = race.trophy_edition

        if input_new_value("flag_edition", race.flag_edition, db_race.flag_edition):
            logger.debug(f"updating {db_race.flag_edition} with {race.flag_edition}")
            db_race.flag_edition = race.flag_edition

        if input_new_value("organizer", race.organizer, db_race.organizer):
            logger.debug(f"updating {db_race.organizer} with {race.organizer}")
            db_race.organizer = race.organizer

        return db_race, Ingestor.Status.MERGED

    @override
    def should_merge_participants(self, *_, **__) -> bool:
        return True

    @override
    def merge_participants(
        self,
        participant: Participant,
        db_participant: Participant,
        status: Ingestor.Status,
    ) -> tuple[Participant, Ingestor.Status]:
        db_participant, status = super().merge_participants(participant, db_participant, status)
        if status != Ingestor.Status.MERGED:
            if input_shoud_create_B_participant(participant):
                logger.debug(f"creating B team participation for {participant=}")
                participant.club_name = (
                    f"{participant.club_name} B" if participant.club_name else f"{participant.club.name} B"
                ).upper()
                return participant, status
            return participant, status

        if input_new_value("distance", participant.distance, db_participant.distance):
            logger.debug(f"updating {db_participant.distance=} with {participant.distance=}")
            db_participant.distance = participant.distance

        return db_participant, Ingestor.Status.MERGED

    @override
    def _get_datasource(self, race: Race, ref_id: str) -> dict | None:
        kwargs = {"sheet_id": self.client.config.sheet_id, "sheet_name": self.client.config.sheet_name}
        datasources = MetadataService.get_datasource_from_race(self.client.DATASOURCE, race, ref_id, **kwargs)
        if len(datasources) > 1:
            logger.warning(f"multiple datasources found for race {race=} and datasource {ref_id=}")
        return datasources[0] if datasources else None

    @override
    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict:
        if not race.url:
            raise ValueError(f"no datasource provided for {race.race_ids[0]}::{race.name}")

        if not self.client.config.sheet_id:
            logger.warning("using default metadata")
            return default_metadata()

        metadata = [
            MetadataBuilder()
            .ref_id(race_id)
            .datasource_name(datasource)
            .values("details_page", race.url)
            .values("sheet_id", self.client.config.sheet_id)
            for race_id in race.race_ids
        ]

        if self.client.config.sheet_name:
            for meta in metadata:
                meta.values("sheet_name", self.client.config.sheet_name)

        return {"datasource": [m.build() for m in metadata]}
