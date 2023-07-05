import logging
from datetime import date
from typing import Tuple, Optional, List

import requests
from bs4 import BeautifulSoup, Tag
from rest_framework.exceptions import ValidationError

from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.actions.digesters import ARCSoupDigester
from apps.entities.services import LeagueService
from apps.participants.models import Participant
from apps.races.models import Race
from apps.schemas import MetadataBuilder
from utils.choices import GENDER_FEMALE, GENDER_MALE

logger = logging.getLogger(__name__)


class ARCClient(Client, source=Datasource.ARC):
    DATASOURCE = Datasource.ARC

    @staticmethod
    def get_race_details_soup(race_id: str, race_name: str = 'unknown', is_female: bool = False, **kwargs) -> Tuple[Tag, str]:
        female = 'ligaete' if is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/regata/{race_id}/{race_name}"

        response = requests.get(url=url, headers=Client.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_races_summary_soup(year: int, is_female: bool = False, **kwargs) -> Tuple[Tag, str]:
        female = 'ligaete' if is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/resultados/{year}"

        response = requests.get(url=url, headers=Client.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_race_results_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    @staticmethod
    def get_club_page_soup(club_id: str, year: int, is_female: bool = False, **kwargs) -> Tuple[Tag, str]:
        female = 'ligaete' if is_female else 'liga-arc'
        url = f'https://www.{female}.com/es/clubes/{year}/{club_id}/1/_/plantilla'
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_web_race_by_id(self, race_id: str, is_female: bool) -> Tuple[Optional[Race], List[Participant]]:
        soup, url = self.get_race_details_soup(race_id=race_id, is_female=is_female)
        digester = ARCSoupDigester(soup=soup)

        name = digester.get_name()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        name = digester.normalize_race_name(name, is_female=is_female)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        edition = digester.get_edition()
        race = Race(
            creation_date=None,
            laps=digester.get_race_laps(),
            lanes=digester.get_race_lanes(),
            town=digester.get_town(),
            type=digester.get_type(),
            date=digester.get_date(),
            day=digester.get_day(),
            cancelled=digester.is_cancelled(),
            cancellation_reasons=[],  # no reason provided by ARC
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=LeagueService.get_by_name(digester.get_league(is_female=is_female)),
            modality=digester.get_modality(),
            organizer=digester.get_organizer(),
            metadata={'datasource': [
                MetadataBuilder()
                .ref_id(race_id)
                .datasource_name(self.DATASOURCE)
                .gender(GENDER_FEMALE if is_female else GENDER_MALE)
                .values("details_page", url)
                .build()
            ]},
        )

        return race, self._find_race_participants(digester, race, is_female)

    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        if not season:
            season = date.today().year
        self._validate_season_gender(season, is_female)
        soup, _ = self.get_races_summary_soup(year=season, is_female=is_female)

        if not soup.find('table', {'class': 'regatas'}):
            logger.error(f'{self.DATASOURCE}: no races found for {season=}')
            return []

        rows = soup.find('table', {'class': 'regatas'}).find_all('tr')
        return [row.find('a')['href'].split('/')[-2] for row in rows]

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################
    @staticmethod
    def _validate_season_gender(season: int, is_female: bool):
        today = date.today()
        if is_female:
            if season < 2018 or season > today.year:
                raise ValidationError({'season': f'Should be between {2018} and {today.year}'})
        else:
            if season < 2009 or season > today.year:
                raise ValidationError({'season': f'Should be between {2009} and {today.year}'})
