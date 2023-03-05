import csv
import logging
from abc import abstractmethod, ABC
from datetime import date
from typing import Optional, List

from apps.actions.management.digesters._item import ScrappedItem
from utils.checks import is_play_off

logger = logging.getLogger(__name__)


class Digester(ABC):
    DATASOURCE: str

    def save(self, items: List[ScrappedItem], file_name: str = None):
        if not len(items):
            return

        file_name = file_name if file_name else f'{self.DATASOURCE}.csv'
        with open(file_name, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(items[0].__dict__.keys())  # write headers
            for item in items:
                writer.writerow(item.__dict__.values())

    @staticmethod
    def is_play_off(name: str) -> bool:
        return is_play_off(name)

    ####################################################
    #                     ABSTRACT                     #
    ####################################################
    @abstractmethod
    def digest(self, **kwargs) -> List[ScrappedItem]:
        raise NotImplementedError

    ####################################################
    #                 ABSTRACT GETTERS                 #
    ####################################################

    @abstractmethod
    def get_name(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_date(self, **kwargs) -> date:
        raise NotImplementedError

    @staticmethod
    def get_edition(**kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_day(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_modality(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_league(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_town(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_organizer(self, **kwargs) -> Optional[str]:
        raise NotImplementedError

    ####################################################

    @abstractmethod
    def get_gender(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_category(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_club_name(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_lane(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_series(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_laps(self, **kwargs) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_distance(self, **kwargs) -> int:
        raise NotImplementedError

    ####################################################

    @abstractmethod
    def normalized_name(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def normalized_club_name(self, **kwargs) -> str:
        raise NotImplementedError

    ####################################################

    @abstractmethod
    def get_race_lanes(self, **kwargs) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_race_laps(self, **kwargs) -> int:
        raise NotImplementedError
