import logging
import time
from collections.abc import Generator
from typing import Any, override

from apps.races.services import MetadataService
from rscraping.data.constants import GENDER_ALL
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace
from rscraping.parsers.html import MultiDayRaceException

from ._ingestor import Ingestor

logger = logging.getLogger(__name__)


class TrainerasIngestor(Ingestor):
    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        race: RSRace | None = None
        participants: list[RSParticipant] = []

        for race_id in self.client.get_race_ids_by_year(year=year):
            if race_id in self._ignored_races or MetadataService.exists(race_id, Datasource.TRAINERAS):
                logger.info(f"ignoring {race_id=}")
                continue

            try:
                time.sleep(1)
                local_race = self.client.get_race_by_id(race_id)

                if not local_race:
                    continue
                if self._is_race_after_today(local_race):
                    # if we reach a race after today, we can stop and yield the current race
                    if race:
                        race.participants = participants
                        logger.info(f"found race for {race_id=}:\n\t{race}")
                        yield race
                    break

                # race changed so we yield the current one and start a new one
                if not race or race.name != local_race.name:
                    if race:
                        race.participants = participants
                        logger.info(f"found race for {race_id=}:\n\t{race}")
                        yield race
                    race = local_race
                    participants = race.participants

                # update current race data
                race.race_ids.append(race_id)
                if race.gender != local_race.gender:
                    race.gender = GENDER_ALL
                participants.extend(local_race.participants)

            except MultiDayRaceException as e:
                time.sleep(1)
                race_1 = self.client.get_race_by_id(race_id, day=1)
                race_2 = self.client.get_race_by_id(race_id, day=2)
                if not race_1 or not race_2:
                    raise e
                if self._is_race_after_today(race_1) or self._is_race_after_today(race_2):
                    break
                logger.info(f"found multiday race for {race_id=}\n{race_1=}\n{race_2=}")
                yield race_1
                yield race_2
                continue

            except ValueError as e:
                logger.error(e)
                continue
