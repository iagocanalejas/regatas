import logging
import re
from abc import abstractmethod, ABC
from datetime import date, time
from typing import Optional, List

from bs4 import Tag

from ai_django.ai_core.utils.strings import find_roman, roman_to_int
from utils.choices import PARTICIPANT_CATEGORY_ABSOLUT, GENDER_FEMALE, GENDER_MALE, RACE_TRAINERA

logger = logging.getLogger(__name__)


class SoupDigester(ABC):
    def __init__(self, soup: Tag):
        self.soup = soup

    def get_edition(self) -> int:
        name = re.sub(r'[\'\".:]', ' ', self.get_name())

        roman_options = [find_roman(w) for w in name.split() if find_roman(w)]
        return roman_to_int(roman_options[0]) if roman_options else 1

    @staticmethod
    def get_modality() -> str:
        return RACE_TRAINERA

    @staticmethod
    def get_gender(is_female: bool) -> str:
        return GENDER_FEMALE if is_female else GENDER_MALE

    @staticmethod
    def get_category() -> str:
        return PARTICIPANT_CATEGORY_ABSOLUT

    @staticmethod
    def get_distance(is_female: bool) -> int:
        return 2778 if is_female else 5556

    ####################################################
    #                     ABSTRACT                     #
    ####################################################

    @abstractmethod
    def get_participants(self, **kwargs) -> List[Tag]:
        raise NotImplementedError

    @abstractmethod
    def get_name(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_date(self, **kwargs) -> Optional[date]:
        raise NotImplementedError

    @abstractmethod
    def get_day(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_league(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_type(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_town(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_organizer(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_race_lanes(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_race_laps(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_cancelled(self, **kwargs) -> bool:
        raise NotImplementedError

    ####################################################

    @abstractmethod
    def get_club_name(self, participant: Tag, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_lane(self, participant: Tag, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_series(self, participant: Tag, **kwargs) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def get_laps(self, participant: Tag, **kwargs) -> List[time]:
        raise NotImplementedError

    ####################################################
    @abstractmethod
    def normalize_race_name(self, name: str, is_female: bool, **kwargs) -> str:
        raise NotImplementedError
