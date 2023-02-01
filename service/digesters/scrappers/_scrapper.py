import logging
import re
from abc import abstractmethod, ABC
from datetime import time, datetime
from typing import Optional, List, Any, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import find_roman, roman_to_int
from digesters._digester import Digester
from digesters._item import ScrappedItem
from utils.checks import is_play_off

logger = logging.getLogger(__name__)


# TODO: Check for disqualified clubs:
#   - https://www.ligalgt.com/principal/regata/66
#   - https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864823
# TODO: Check for cancelled races:
#   - https://www.ligalgt.com/principal/regata/114
class Scrapper(Digester, ABC):
    _excluded_ids: List[Any]  # weird races

    HEADERS = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Cache-Control': 'max-age=0'
    }

    @staticmethod
    def is_play_off(name: str) -> bool:
        return is_play_off(name)

    def digest(self, **kwargs) -> List[ScrappedItem]:
        return self.scrap(**kwargs)

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

    ####################################################
    #              NORMALIZATION METHODS               #
    ####################################################

    @staticmethod
    def normalize_time(value: str) -> Optional[time]:
        parts = re.findall(r'\d+', value)
        if len(parts) == 2:
            # try to fix '2102:48' | '25:2257' page errors
            if len(parts[0]) == 4:
                return datetime.strptime(f'{parts[0][0:2]}:{parts[0][2:]},{parts[1]}', '%M:%S,%f').time()
            if len(parts[1]) == 4:
                return datetime.strptime(f'{parts[0]}:{parts[1][0:2]},{parts[1][2:]}', '%M:%S,%f').time()
            return datetime.strptime(f'{parts[0]}:{parts[1]}', '%M:%S').time()
        if len(parts) == 3:
            return datetime.strptime(f'{parts[0]}:{parts[1]},{parts[2]}', '%M:%S,%f').time()
        return None
