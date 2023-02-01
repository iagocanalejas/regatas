import logging
import re
from abc import abstractmethod, ABC
from typing import List, Any, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import find_roman, roman_to_int
from apps.entities.models import LEAGUE_GENDER_FEMALE, LEAGUE_GENDER_MALE
from apps.races.models import RACE_TRAINERA
from digesters._digester import Digester
from digesters._item import ScrappedItem

logger = logging.getLogger(__name__)


# TODO: Check for disqualified clubs:
#   - https://www.ligalgt.com/principal/regata/66
#   - https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864823
# TODO: Check for cancelled races:
#   - https://www.ligalgt.com/principal/regata/114
class Scrapper(Digester, ABC):
    _excluded_ids: List[Any]  # weird races
    _is_female: bool = False

    HEADERS = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Cache-Control': 'max-age=0'
    }

    def digest(self, **kwargs) -> List[ScrappedItem]:
        # route 'digest' method to abstract 'scrap'
        return self.scrap(**kwargs)

    def get_gender(self, **kwargs) -> str:
        return LEAGUE_GENDER_FEMALE if self._is_female else LEAGUE_GENDER_MALE

    def get_modality(self, **kwargs) -> str:
        return RACE_TRAINERA

    @staticmethod
    def get_edition(name: str, **kwargs) -> int:
        name = re.sub(r'[\'\".:]', ' ', name)

        roman_options = [find_roman(w) for w in name.split() if find_roman(w)]
        return roman_to_int(roman_options[0]) if roman_options else 1

    ####################################################
    #                     ABSTRACT                     #
    ####################################################
    @abstractmethod
    def scrap(self, **kwargs) -> List[ScrappedItem]:
        raise NotImplementedError

    ####################################################
    #                 ABSTRACT GETTERS                 #
    ####################################################
    @abstractmethod
    def get_summary_soup(self, **kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @abstractmethod
    def get_race_details_soup(self, race_id: str, **kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError
