import logging
import os
from collections.abc import Generator
from os.path import isfile
from typing import Any, override

from rscraping.data.models import Race as RSRace

from ._ingester import Ingester

logger = logging.getLogger(__name__)


class FolderIngester(Ingester):
    def __init__(self, path: str):
        self.path = path

    @override
    def fetch(self, *_, **kwargs) -> Generator[RSRace, Any, Any]:
        if os.path.isfile(self.path):
            race = self._process_file(self.path)
            if race:
                yield race
            os.remove(self.path)
            return

        for file_name in os.listdir(self.path):
            file = os.path.join(self.path, file_name)
            race = self._process_file(file)
            if race:
                yield race
            os.remove(file)

    @override
    def fetch_by_ids(self, *_, **__) -> Generator[RSRace, Any, Any]:
        return self.fetch()

    def _process_file(self, file: str) -> RSRace | None:
        if isfile(file) and file.endswith(".json"):
            logger.info(f"processing {file=}")
            with open(file) as race_file:
                return RSRace.from_json(race_file.read())
