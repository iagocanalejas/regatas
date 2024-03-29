import logging
import time
from collections.abc import Generator
from typing import Any, override

from apps.races.services import MetadataService
from rscraping.data.constants import GENDER_ALL
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace
from rscraping.parsers.html import MultiRaceException

from ._ingestor import Ingestor

logger = logging.getLogger(__name__)


class TrainerasIngestor(Ingestor):
    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        race: RSRace | None = None
        participants: list[RSParticipant] = []

        for race_id in self.client.get_race_ids_by_year(year=year):
            for local_race in self._retrieve_race(race_id):
                if self._is_race_after_today(local_race):
                    # if we reach a race after today, we can stop and yield the current race
                    if race:
                        race.participants = participants
                        logger.debug(f"found race for {year=}:\n\t{race}")
                        yield race
                    break

                # race changed so we yield the current one and start a new one
                if not race or race.name != local_race.name:
                    if race:
                        race.participants = participants
                        logger.debug(f"found race for {year=}:\n\t{race}")
                        yield race
                    race = local_race
                    participants = race.participants

                # update current race data
                race.race_ids.append(race_id)
                if race.gender != local_race.gender:
                    race.gender = GENDER_ALL
                participants.extend(local_race.participants)

        # yield the last race
        if race:
            race.participants = participants
            logger.debug(f"found race for {year=}:\n\t{race}")
            yield race

    @override
    def _retrieve_race(self, race_id: str) -> Generator[RSRace, Any, Any]:
        if race_id in self._ignored_races or MetadataService.exists(Datasource.TRAINERAS, race_id):
            logger.debug(f"ignoring {race_id=}")
            return

        try:
            time.sleep(1)
            race = self.client.get_race_by_id(race_id)
            if race:
                yield race
        except MultiRaceException:
            table= 1
            while True:
                time.sleep(1)
                race = self.client.get_race_by_id(race_id, table=table)
                if not race:
                    break
                logger.debug(f"found multi race for {race_id=}:\n\t{race}")
                yield race
        except ValueError as e:
            logger.error(e)
            return
