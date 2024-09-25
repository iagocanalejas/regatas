import logging
import time
from collections.abc import Generator
from datetime import date, datetime
from typing import override

from apps.entities.models import Entity
from apps.races.services import MetadataService
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
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace]:
        for race_id in self.client.get_race_ids_by_year(year=year):
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_last_weekend(self, **kwargs) -> Generator[RSRace]:
        for race_id in self.client.get_last_weekend_race_ids():
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_by_ids(self, race_ids: list[str], table: int | None = None, **_) -> Generator[RSRace]:
        for race_id in race_ids:
            race = self.client.get_race_by_id(race_id, table=table)
            if race:
                logger.debug(f"found race for {race_id=}:\n\t{race}")
                yield race
            time.sleep(1)

    @override
    def fetch_by_entity(self, entity: Entity, year: int, **kwargs) -> Generator[RSRace]:
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
    def fetch_by_club(self, club_id: str, year: int, **kwargs) -> Generator[RSRace]:
        for race_id in self.client.get_race_ids_by_club(club_id=club_id, year=year):
            for race in self._retrieve_race(race_id):
                if race and self._is_race_after_today(race):
                    break
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def fetch_by_flag(self, *args, **kwargs) -> Generator[RSRace]:
        raise NotImplementedError

    @override
    def fetch_by_url(self, url: str, **kwargs) -> RSRace | None:
        return self.client.get_race_by_url(url, **kwargs)

    @override
    def _retrieve_race(self, race_id: str) -> Generator[RSRace]:
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
