import logging
from collections.abc import Generator
from typing import Any, override

from apps.actions.management.helpers.input import input_update_value
from apps.participants.models import Participant
from apps.races.models import Race
from apps.races.services import MetadataService
from rscraping import Datasource
from rscraping.clients import TabularDataClient
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Race as RSRace
from rscraping.data.normalization.leagues import normalize_league_name

from ._ingestor import Ingestor

logger = logging.getLogger(__name__)


class TabularIngestor(Ingestor):
    def __init__(self, client: TabularDataClient, ignored_races: list[str]):
        self.client = client
        self._ignored_races = ignored_races

    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_race_ids_by_year(year=year):
            if race_id in self._ignored_races or MetadataService.exists(race_id, Datasource.TABULAR):
                continue

            race = self.client.get_race_by_id(race_id)
            if not race:
                continue
            logger.info(f"found race for {race_id=}:\n\t{race}")

            race.league = (
                normalize_league_name(race.league, is_female=race.gender == GENDER_FEMALE) if race.league else None
            )
            yield race

    @override
    def merge(self, race: Race, db_race: Race) -> tuple[Race, bool]:
        db_race, should_merge = super().merge(race, db_race)
        if not should_merge:
            return race, False

        if race.trophy_edition != db_race.trophy_edition and input_update_value(
            "trophy_edition", race.trophy_edition, db_race.trophy_edition
        ):
            logger.info(f"updating {db_race.trophy_edition=} with {race.trophy_edition=}")
            db_race.trophy_edition = race.trophy_edition

        if race.flag_edition != db_race.flag_edition and input_update_value(
            "flag_edition", race.flag_edition, db_race.flag_edition
        ):
            logger.info(f"updating {db_race.flag_edition} with {race.flag_edition}")
            db_race.flag_edition = race.flag_edition

        if race.organizer != db_race.organizer and input_update_value("organizer", race.organizer, db_race.organizer):
            logger.info(f"updating {db_race.organizer} with {race.organizer}")
            db_race.organizer = race.organizer

        return db_race, True

    @override
    def merge_participants(self, participant: Participant, db_participant: Participant) -> tuple[Participant, bool]:
        db_participant, should_merge = super().merge_participants(participant, db_participant)
        if not should_merge:
            return participant, False

        logger.info(f"merging {participant=} and {db_participant=}")
        if participant.distance != db_participant.distance and input_update_value(
            "distance", participant.distance, db_participant.distance
        ):
            logger.info(f"updating {db_participant.distance=} with {participant.distance=}")
            db_participant.distance = participant.distance

        if participant.lane != db_participant.lane and input_update_value(
            "lane", participant.lane, db_participant.lane
        ):
            logger.info(f"updating {db_participant.lane=} with {participant.lane=}")
            db_participant.lane = participant.lane

        return db_participant, True
