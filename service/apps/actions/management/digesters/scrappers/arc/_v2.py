import logging
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_parenthesis
from apps.actions.clients import ARCClient
from apps.actions.datasource import Datasource
from apps.actions.management.digesters._item import ScrappedItem
from apps.actions.management.digesters.scrappers.arc.arc import ARCScrapper
from apps.entities.normalization import normalize_club_name
from apps.participants.normalization import normalize_lap_time
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ARCScrapperV2(ARCScrapper, version=Datasource.ARCVersions.V2):
    DATASOURCE = Datasource.ARCVersions.V2
    _excluded_ids = []
    _client: ARCClient = ARCClient(source=Datasource.ARC)

    def scrap(self) -> List[ScrappedItem]:
        if self._year > date.today().year:
            raise StopProcessing

        soup, summary_url = self._client.get_races_summary_soup(year=self._year)

        race_ids = self.__get_race_ids(soup)
        if len(race_ids) == 0:
            raise StopProcessing

        for race_id, race_name in [(r, n) for (r, n) in race_ids if r not in self._excluded_ids]:
            details_soup, url = self._client.get_race_details_soup(race_id=race_id, race_name=race_name, is_female=self._is_female)

            name = self.get_name(details_soup)
            league = self.get_league(details_soup)

            # data parsed from the name
            trophy_name = self.normalized_name(name)
            edition = self.get_edition(name)
            day = self.get_day(name)

            # retrieve data from race summary
            race_summary = details_soup.find('div', {'class': 'articulo detalles'}) \
                .find('div', {'class': 'grid_5 alpha'})

            t_date = self.get_date(race_summary)
            town = self.get_town(race_summary)
            race_lanes = self.get_race_lanes(race_summary)
            race_laps = self.get_race_laps(race_summary)

            # known hardcoded mappings too specific to be implemented
            trophy_name, edition, day = self._client.normalize('edition', trophy_name, year=self._year, edition=edition, day=day)

            tables = details_soup.find_all('table', {'class': 'clasificacion tanda'})
            series = 1
            for table in tables:
                results = table.find('tbody').find_all('tr')
                for result in results:
                    club_name = self.get_club_name(result)
                    yield ScrappedItem(
                        name=name,
                        t_date=t_date,
                        edition=edition,
                        day=day,
                        modality=self.get_modality(),
                        league=league,
                        town=town,
                        organizer=self.get_organizer(),
                        gender=self.get_gender(),
                        category=self.get_category(),
                        club_name=club_name,
                        lane=self.get_lane(result),
                        series=series,
                        laps=self.get_laps(result),
                        distance=self.get_distance(),
                        trophy_name=trophy_name,
                        participant=self.normalized_club_name(club_name),
                        race_id=race_id,
                        url=url,
                        datasource=Datasource.ARC,
                        race_laps=race_laps,
                        race_lanes=race_lanes,
                    )
                series += 1

    ####################################################
    #                      GETTERS                     #
    ####################################################
    @staticmethod
    def get_name(soup: Tag, **kwargs) -> str:
        return soup.select_one('div[class*="resultado"]').find('h2').text.strip().upper()

    @staticmethod
    def get_date(soup: Tag, **kwargs) -> date:
        text = soup.find_all('li')[0].text.upper().replace('FECHA', '')
        text = text.replace('AGO', 'AUG')  # want to avoid changing the locale
        return datetime.strptime(text.strip(), '%d %b %Y').date()

    def get_day(self, name: str, **kwargs) -> int:
        if self.is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\d+ª día|\(\d+ª? JORNADA\)', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    def get_league(self, soup: Tag, **kwargs) -> str:
        if self._is_female:
            return 'EMAKUMEZKO TRAINERUEN ELKARTEA'
        text = whitespaces_clean(soup.find('h1', {'class': 'seccion'}).find('span').text).upper()
        if self.is_play_off(text):
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO'
        return re.sub(r'TEMPORADA \d+ GRUPO', 'ASOCIACIÓN DE REMO DEL CANTÁBRICO', text)

    @staticmethod
    def get_town(soup: Tag, **kwargs) -> Optional[str]:
        li = soup.find_all('li')
        if len(li) < 4:
            return None  # no town
        text = remove_parenthesis(li[3].text)
        text = text.replace(' Ver mapaOcultar mapa', '')
        return whitespaces_clean(text).upper()

    def get_organizer(self, **kwargs) -> Optional[str]:
        return None

    @staticmethod
    def get_club_name(soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[0].text

    @staticmethod
    def get_lane(soup: Tag, **kwargs) -> int:
        return int(soup.find_all('th')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [e.text for e in soup.find_all('td')[1:] if e.text]
        times = [t for t in [normalize_lap_time(e) for e in times] if t is not None]
        return [t.isoformat() for t in times if t.isoformat() != '00:00:00']

    def normalized_name(self, name: str, **kwargs) -> str:
        return self._client.normalize('race_name', name, is_female=self._is_female)

    @staticmethod
    def normalized_club_name(name: str, **kwargs) -> str:
        return normalize_club_name(name)

    @staticmethod
    def get_race_lanes(soup: Tag, **kwargs) -> int:
        text = soup.find_all('li')[2].text.upper()
        if 'CONTRARRELOJ' in text:
            return 1
        return int(re.findall(r'\d+', text)[0])

    @staticmethod
    def get_race_laps(soup: Tag, **kwargs) -> int:
        return int(re.findall(r'\d+', soup.find_all('li')[2].text)[1])

    def get_series(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    @staticmethod
    def __get_race_ids(soup: Tag) -> List[Tuple[int, str]]:
        if not soup.find('table', {'class': 'regatas'}):
            logger.error(f'not races found')
            return []

        rows = soup.find('table', {'class': 'regatas'}).find_all('tr')
        return [(row.find('a')['href'].split('/')[-2], row.find('a')['href'].split('/')[-1]) for row in rows]
