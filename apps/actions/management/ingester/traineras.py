import logging
import time
from collections.abc import Generator
from typing import override

from apps.races.services import MetadataService
from rscraping.clients import TrainerasClient
from rscraping.data.constants import GENDER_ALL
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace
from rscraping.parsers.html import MultiRaceException

from ._ingester import Ingester

logger = logging.getLogger(__name__)


class TrainerasIngester(Ingester):
    @override
    def fetch(self, *_, year: int, **kwargs) -> Generator[RSRace]:
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
    def fetch_last_weekend(self, **kwargs) -> Generator[RSRace]:
        race: RSRace | None = None
        participants: list[RSParticipant] = []

        for race_id in self.client.get_last_weekend_race_ids():
            for local_race in self._retrieve_race(race_id):
                if self._is_race_after_today(local_race):
                    # if we reach a race after today, we can stop and yield the current race
                    if race:
                        race.participants = participants
                        logger.debug(f"found last weekend race:\n\t{race}")
                        yield race
                    break

                # race changed so we yield the current one and start a new one
                if not race or race.name != local_race.name:
                    if race:
                        race.participants = participants
                        logger.debug(f"found last weekend race:\n\t{race}")
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
            logger.debug(f"found last weekend race:\n\t{race}")
            yield race

    @override
    def fetch_by_flag(
        self,
        *_,
        flag_id: str,
        include_existing: bool = False,
        only_new: bool = False,
        **kwargs,
    ) -> Generator[RSRace]:
        assert isinstance(self.client, TrainerasClient)

        # when searching for new races we want to start from the most recent ones
        race_ids = (
            reversed(list(self.client.get_race_ids_by_flag(flag_id)))
            if only_new
            else self.client.get_race_ids_by_flag(flag_id)
        )

        for race_id in race_ids:
            races = list(self._retrieve_race(race_id, include_existing))
            if not races and only_new:
                # if we are only looking for new races once we find an existing one we can stop
                logger.info(f"ignoring {race_id=} as {only_new=} and the last one already exists")
                return
            for race in races:
                if race:
                    logger.debug(f"found race for {race_id=}:\n\t{race}")
                    yield race

    @override
    def _retrieve_race(self, race_id: str, include_existing: bool = False) -> Generator[RSRace]:
        if race_id in self._ignored_races:
            logger.debug(f"ignoring {race_id=}")
            return
        if not include_existing and MetadataService.exists(Datasource.TRAINERAS, race_id):
            logger.debug(f"{race_id=} already in database")
            return

        try:
            time.sleep(1)
            race = self.client.get_race_by_id(race_id)
            if race:
                yield race
        except MultiRaceException:
            table = 1
            while True:
                time.sleep(1)
                race = self.client.get_race_by_id(race_id, table=table)
                if not race:
                    break
                logger.debug(f"found multi race for {race_id=}:\n\t{race}")
                table += 1
                yield race
        except ValueError as e:
            logger.error(e)
        return
