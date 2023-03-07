import datetime
import logging
from typing import List, Optional, Tuple

import requests
from bs4 import Tag, BeautifulSoup
from rest_framework.exceptions import ValidationError

from apps.actions.clients._client import Client
from apps.actions.datasource import Datasource
from apps.actions.digesters import ACTSoupDigester
from apps.entities.services import LeagueService
from apps.participants.models import Participant
from apps.races.models import Race
from utils.choices import RACE_TRAINERA

logger = logging.getLogger(__name__)


class ACTClient(Client, source=Datasource.ACT):
    DATASOURCE = Datasource.ACT

    @staticmethod
    def get_race_details_soup(race_id: str, is_female: bool, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if is_female else ''
        url = f'https://www.euskolabelliga.com{female}/resultados/ver.php?r={race_id}'
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_races_summary_soup(year: int, is_female: bool, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if is_female else ''
        url = f"https://www.euskolabelliga.com{female}/resultados/index.php?t={year}"
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_race_results_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    def get_web_race_by_id(self, race_id: str, is_female: bool) -> Tuple[Optional[Race], List[Participant]]:
        soup, url = self.get_race_details_soup(race_id, is_female)
        digester = ACTSoupDigester(soup=soup)

        name = digester.get_name()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        # parse name, edition, and date from the page title (<edition> <race_name> (<date>))
        edition = digester.get_edition()
        t_date = digester.get_date()
        day = digester.get_day()
        ttype = digester.get_type()

        name = digester.normalize_race_name(name, is_female=is_female)
        name, edition = digester.hardcoded_name_edition(name, is_female=is_female, year=t_date.year, edition=edition)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        race = Race(
            creation_date=None,
            laps=digester.get_race_laps(),
            lanes=digester.get_race_lanes(),
            town=digester.get_town(),
            type=ttype,
            date=t_date,
            day=day,
            cancelled=digester.is_cancelled(),
            cancellation_reasons=None,  # no reason provided by ACT
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=LeagueService.get_by_name(digester.get_league(is_female=is_female)),
            modality=RACE_TRAINERA,
            organizer=self._find_organizer(digester.get_organizer()),
            metadata=Race.MetadataBuilder().race_id(race_id).datasource_name(self.DATASOURCE).values("details_page", url).build(),
        )
        return race, self._find_race_participants(digester, race, is_female=is_female)

    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        if not season:
            season = datetime.date.today().year
        self._validate_season_gender(season, is_female)
        soup, _ = self.get_races_summary_soup(year=season, is_female=is_female)

        if not soup.find('div', {'class': 'zutabe_ezkerra'}):
            logger.error(f'{self.DATASOURCE}: no races found for {season=}')
            return []

        table = soup.find('table', {'class': 'taula tablepadding'})
        rows = table.find('tbody').find_all('tr')

        return [row.find('td', {'class': 'race_name'}).find('a')['href'].split('=')[-1] for row in rows]

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################
    @staticmethod
    def _validate_season_gender(season: int, is_female: bool):
        today = datetime.date.today()
        if is_female:
            if season < 2009 or season > today.year:
                raise ValidationError({'season': f'Should be between {2009} and {today.year}'})
        else:
            if season < 2003 or season > today.year:
                raise ValidationError({'season': f'Should be between {2003} and {today.year}'})
