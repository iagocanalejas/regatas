import logging
from typing import override

from apps.schemas import default_metadata

from ._digester import Digester

logger = logging.getLogger(__name__)


class FolderDigester(Digester):
    def __init__(self, path: str):
        self.path = path

    @override
    def _build_metadata(self, *_, **__) -> dict:
        return default_metadata()
