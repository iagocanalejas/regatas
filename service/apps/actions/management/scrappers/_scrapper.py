import logging
from abc import abstractmethod, ABC
from typing import List, Any

from apps.actions.clients import Client
from apps.actions.management.utils import ScrappedItem

logger = logging.getLogger(__name__)


# TODO: Check for disqualified clubs:
#   - https://www.ligalgt.com/principal/regata/66
#   - https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864823
class Scrapper(ABC):
    DATASOURCE: str
    _client: Client
    _excluded_ids: List[Any]  # weird races
    _is_female: bool

    ####################################################
    #                     ABSTRACT                     #
    ####################################################
    @abstractmethod
    def scrap(self, **kwargs) -> List[ScrappedItem]:
        raise NotImplementedError
