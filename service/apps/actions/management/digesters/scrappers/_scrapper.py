import logging
from abc import abstractmethod, ABC
from typing import List, Any

from apps.actions.clients import Client
from apps.actions.management.digesters import Digester
from apps.actions.management.digesters._item import ScrappedItem
from utils.choices import RACE_TRAINERA, GENDER_FEMALE, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT

logger = logging.getLogger(__name__)


# TODO: Check for disqualified clubs:
#   - https://www.ligalgt.com/principal/regata/66
#   - https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864823
class Scrapper(Digester, ABC):
    _client: Client
    _excluded_ids: List[Any]  # weird races
    _is_female: bool = False

    def digest(self, **kwargs) -> List[ScrappedItem]:
        # route 'digest' method to abstract 'scrap'
        return self.scrap(**kwargs)

    def get_edition(self, name: str, **kwargs) -> int:
        return self._client.get_edition(name)

    def get_modality(self, **kwargs) -> str:
        return RACE_TRAINERA

    def get_gender(self, **kwargs) -> str:
        return GENDER_FEMALE if self._is_female else GENDER_MALE

    def get_category(self, **kwargs) -> str:
        return PARTICIPANT_CATEGORY_ABSOLUT

    def get_distance(self, **kwargs) -> int:
        return 2778 if self._is_female else 5556

    ####################################################
    #                     ABSTRACT                     #
    ####################################################
    @abstractmethod
    def scrap(self, **kwargs) -> List[ScrappedItem]:
        raise NotImplementedError
