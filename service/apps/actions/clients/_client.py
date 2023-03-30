import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List

from bs4 import Tag

from ai_django.ai_core.utils.strings import roman_to_int, find_roman
from apps.actions.digesters import SoupDigester
from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService
from apps.participants.models import Participant
from apps.races.models import Race, Trophy, Flag
from apps.races.services import RaceService, TrophyService, FlagService

logger = logging.getLogger(__name__)


class Client(ABC):
    _registry = {}

    DATASOURCE: str
    HEADERS = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Cache-Control': 'max-age=0'
    }

    def __init_subclass__(cls, **kwargs):
        source = kwargs.pop('source', None)
        super().__init_subclass__(**kwargs)
        if source:
            cls._registry[source] = cls

    def __new__(cls, source: str, **kwargs) -> 'Client':  # pragma: no cover
        subclass = cls._registry[source]
        final_obj = object.__new__(subclass)

        return final_obj

    @staticmethod
    def get_edition(name: str) -> int:
        name = re.sub(r'[\'\".:]', ' ', name)

        roman_options = [find_roman(w) for w in name.split() if find_roman(w)]
        return roman_to_int(roman_options[0]) if roman_options else 1

    def get_db_race_by_id(self, race_id: str) -> Tuple[Optional[Race], List[Participant]]:
        db_race = self._find_race_in_db(race_id, datasource=self.DATASOURCE)
        return db_race, db_race.participants.select_related('club').all() if db_race else []

    ####################################################
    #                     ABSTRACT                     #
    ####################################################

    @staticmethod
    @abstractmethod
    def get_race_details_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_races_summary_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_race_results_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_club_page_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @abstractmethod
    def get_web_race_by_id(self, race_id: str, is_female: bool) -> Tuple[Optional[Race], List[Participant]]:
        raise NotImplementedError

    @abstractmethod
    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        raise NotImplementedError

    ####################################################
    #                PROTECTED METHODS                 #
    ####################################################
    def _find_race_participants(self, digester: SoupDigester, race: Race, is_female: bool) -> List[Participant]:
        for participant in digester.get_participants():
            club_name = digester.get_club_name(participant)
            yield Participant(
                race=race,
                club_name=club_name,
                club=self._find_club(club_name),
                distance=digester.get_distance(is_female=is_female),
                laps=digester.get_laps(participant),
                lane=digester.get_lane(participant),
                series=digester.get_series(participant),
                gender=digester.get_gender(is_female=is_female),
                category=digester.get_category(),
            )

    @staticmethod
    def _find_race_in_db(race_id: str, datasource: str) -> Optional[Race]:
        try:
            return RaceService.get_filtered(
                queryset=Race.objects,
                filters={
                    'metadata': [{
                        "ref_id": race_id,
                        "datasource_name": datasource.lower()
                    }]
                },
                prefetch=['participants'],
            ).get()
        except Race.DoesNotExist:
            return None

    @staticmethod
    def _find_trophy_or_flag(name: str) -> Tuple[Optional[Trophy], Optional[Flag]]:
        found_trophy = found_flag = None
        try:
            found_trophy = TrophyService.get_closest_by_name(name)
            logger.info(f'found {found_trophy=}')
        except Trophy.DoesNotExist:
            pass
        try:
            found_flag = FlagService.get_closest_by_name(name)
            logger.info(f'found {found_flag=}')
        except Flag.DoesNotExist:
            pass
        return found_trophy, found_flag

    @staticmethod
    def _find_club(name: str) -> Optional[Entity]:
        logger.info(f'found participant {name=}')
        name = normalize_club_name(name)
        logger.info(f'normalized {name=}')
        try:
            found_club = EntityService.get_closest_club_by_name(name)
            logger.info(f'found {found_club=}')
            return found_club
        except Entity.DoesNotExist:
            logger.error(f'no matching club found for {name=}')
            return None

    @staticmethod
    def _find_organizer(name: str) -> Optional[Entity]:
        if not name:
            return None
        try:
            found_organizer = EntityService.get_closest_by_name_type(name, entity_type=None)
            logger.info(f'found {found_organizer=}')
            return found_organizer
        except Entity.DoesNotExist:
            return None
