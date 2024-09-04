import logging
from collections.abc import Generator
from typing import override

from apps.races.services import MetadataService
from rscraping.clients import TabularDataClient
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace
from rscraping.data.normalization.leagues import normalize_league_name

from ._ingester import Ingester

logger = logging.getLogger(__name__)


class TabularIngester(Ingester):
    client: TabularDataClient

    def __init__(self, client: TabularDataClient, ignored_races: list[str]):
        self.client = client
        self._ignored_races = ignored_races

    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace]:
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
