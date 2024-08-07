import logging
import time
from collections.abc import Generator
from datetime import date, datetime
from typing import Any, override

from apps.actions.management.helpers.input import (
    input_competition,
)
from apps.actions.management.helpers.retrieval import retrieve_competition, retrieve_entity
from apps.entities.models import Entity, League
from apps.entities.normalization import normalize_club_name
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, MetadataService, RaceService, TrophyService
from rscraping.clients import ClientProtocol
from rscraping.data.models import Race as RSRace

from ._protocol import IngesterProtocol

logger = logging.getLogger(__name__)


class Ingester(IngesterProtocol):
    def __init__(self, client: ClientProtocol, ignored_races: list[str]):
        self.client = client
        self._ignored_races = ignored_races

    @staticmethod
    def _is_race_after_today(race: RSRace) -> bool:
        return datetime.strptime(race.date, "%d/%m/%Y").date() > date.today()

    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_race_ids_by_year(year=year):
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_last_weekend(self, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_last_weekend_race_ids():
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_by_ids(self, race_ids: list[str], table: int | None = None, **_) -> Generator[RSRace, Any, Any]:
        for race_id in race_ids:
            race = self.client.get_race_by_id(race_id, table=table)
            if race:
                logger.debug(f"found race for {race_id=}:\n\t{race}")
                yield race
            time.sleep(1)

    @override
    def fetch_by_entity(self, entity: Entity, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        sources = [
            datasource
            for datasource in entity.metadata.get("datasource", [])
            if datasource["datasource_name"] == self.client.DATASOURCE.value.lower()
        ]
        ref_id = sources[0]["ref_id"] if sources else None

        if not ref_id:
            logger.warning(f"no ref_id found for {entity=} in {self.client.DATASOURCE}")
            return

        yield from self.fetch_by_club(ref_id, year, **kwargs)

    @override
    def fetch_by_club(self, club_id: str, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        for race_id in self.client.get_race_ids_by_club(club_id=club_id, year=year):
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_by_flag(self, *args, **kwargs) -> Generator[RSRace, Any, Any]:
        raise NotImplementedError

    @override
    def fetch_by_url(self, url: str, **kwargs) -> RSRace | None:
        return self.client.get_race_by_url(url, **kwargs)

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

    @override
    def _retrieve_race(self, race_id: str) -> Generator[RSRace, Any, Any]:
        if race_id in self._ignored_races or MetadataService.exists(self.client.DATASOURCE, race_id):
            logger.debug(f"ignoring {race_id=}")
            return

        try:
            time.sleep(1)
            race = self.client.get_race_by_id(race_id)
            if race:
                yield race
        except ValueError as e:
            logger.error(e)
            return
