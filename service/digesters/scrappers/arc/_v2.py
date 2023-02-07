import logging
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import requests
from bs4 import Tag, BeautifulSoup

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_parenthesis, int_to_roman
from apps.entities.normalization import normalize_club_name
from apps.races.normalization import normalize_trophy_name
from digesters._item import ScrappedItem
from digesters.scrappers.arc.arc import ARCScrapper, ARC_V2
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ARCScrapperV2(ARCScrapper, version=ARC_V2):
    _excluded_ids = []

    def scrap(self) -> List[ScrappedItem]:
        if self._year > date.today().year:
            raise StopProcessing

        soup, summary_url = self.get_summary_soup()

        race_ids = self.__get_race_ids(soup)
        if len(race_ids) == 0:
            raise StopProcessing

        for race_id, race_name in [(r, n) for (r, n) in race_ids if r not in self._excluded_ids]:
            details_soup, url = self.get_race_details_soup(race_id, race_name=race_name)

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
            trophy_name, edition, day = self.__hardcoded_mappings(trophy_name, edition, day)

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
                        datasource=self.DATASOURCE,
                        race_laps=race_laps,
                        race_lanes=race_lanes,
                    )
                series += 1

    ####################################################
    #                      GETTERS                     #
    ####################################################

    def get_summary_soup(self) -> Tuple[Tag, str]:
        female = 'ligaete' if self._is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/resultados/{self._year}"

        response = requests.get(url=url, headers=self.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    def get_race_details_soup(self, race_id: str, race_name: str = None) -> Tuple[Tag, str]:
        female = 'ligaete' if self._is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/regata/{race_id}/{race_name}"

        response = requests.get(url=url, headers=self.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    def get_league(self, soup: Tag, **kwargs) -> str:
        if self._is_female:
            return 'EMAKUMEZKO TRAINERUEN ELKARTEA'
        text = whitespaces_clean(soup.find('h1', {'class': 'seccion'}).find('span').text).upper()
        if self.is_play_off(text):
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO'
        return re.sub(r'TEMPORADA \d+ GRUPO', 'ASOCIACIÓN DE REMO DEL CANTÁBRICO', text)

    @staticmethod
    def get_name(soup: Tag, **kwargs) -> str:
        return soup.select_one('div[class*="resultado"]').find('h2').text.strip().upper()

    def normalized_name(self, name: str, **kwargs) -> str:
        name = name.replace('AYTO', 'AYUNTAMIENTO')
        name = name.replace('IKURRINA', 'IKURRIÑA')
        name = name.replace(' AE ', '')
        name = re.sub(r'EXCMO|ILTMO', '', name)
        name = whitespaces_clean(name)

        # remove edition
        edition = int_to_roman(self.get_edition(name))
        name = ' '.join(n for n in re.sub(r'[\'\".:]', ' ', name).split() if n != edition)
        # remove day
        name = re.sub(r'\d+ª día|\(\d+ª? JORNADA\)', '', name)

        name = self.__remove_waste_name_parts(name)
        name = normalize_trophy_name(name, self._is_female)

        return name

    def get_day(self, name: str, **kwargs) -> int:
        if self.is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\d+ª día|\(\d+ª? JORNADA\)', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    @staticmethod
    def get_date(soup: Tag, **kwargs) -> date:
        text = soup.find_all('li')[0].text.upper().replace('FECHA', '')
        text = text.replace('AGO', 'AUG')  # want to avoid changing the locale
        return datetime.strptime(text.strip(), '%d %b %Y').date()

    @staticmethod
    def get_town(soup: Tag, **kwargs) -> Optional[str]:
        li = soup.find_all('li')
        if len(li) < 4:
            return None  # no town
        text = remove_parenthesis(li[3].text)
        text = text.replace(' Ver mapaOcultar mapa', '')
        return whitespaces_clean(text).upper()

    @staticmethod
    def get_club_name(soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[0].text

    @staticmethod
    def normalized_club_name(name: str, **kwargs) -> str:
        return normalize_club_name(name)

    @staticmethod
    def get_lane(soup: Tag, **kwargs) -> int:
        return int(soup.find_all('th')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [e.text for e in soup.find_all('td')[1:] if e.text]
        times = [t for t in [self.normalize_time(e) for e in times] if t is not None]
        return [t.isoformat() for t in times if t.isoformat() != '00:00:00']

    @staticmethod
    def get_race_lanes(soup: Tag, **kwargs) -> int:
        text = soup.find_all('li')[2].text.upper()
        if 'CONTRARRELOJ' in text:
            return 1
        return int(re.findall(r'\d+', text)[0])

    @staticmethod
    def get_race_laps(soup: Tag, **kwargs) -> int:
        return int(re.findall(r'\d+', soup.find_all('li')[2].text)[1])

    def get_organizer(self, **kwargs) -> Optional[str]:
        return None

    def get_series(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def __hardcoded_mappings(self, name: str, edition: int, day: int) -> Tuple[str, int, int]:
        if 'AMBILAMP' in name:
            return 'BANDERA AMBILAMP', edition, day
        if 'BANDERA DE CASTRO' in name or 'BANDERA CIUDAD DE CASTRO' in name:
            return 'BANDERA DE CASTRO', edition, day
        if 'CORREO' in name and 'IKURRIÑA' in name:
            return 'EL CORREO IKURRIÑA', (self._year - 1986), day
        if 'DONIBANE ZIBURUKO' in name:
            return 'DONIBANE ZIBURUKO ESTROPADAK', int(re.findall(r'\d+', name)[0]), 1
        if 'SAN VICENTE DE LA BARQUERA' in name:
            return 'BANDERA SAN VICENTE DE LA BARQUERA', edition, day

        match = re.match(r'\d+ª? JORNADA|JORNADA \d+', name)
        if match:
            arc = 1 if '1' in name else '2'
            return f'REGATA LIGA ARC {arc}', edition, int(re.findall(r'\d+', match.group(0))[0])

        if self.is_play_off(name):
            return 'PLAY-OFF ARC', (self._year - 2005), day

        return name, edition, day

    @staticmethod
    def __remove_waste_name_parts(name: str) -> str:
        if '-' not in name:
            return name
        part1, part2 = whitespaces_clean(name.split('-')[0]), whitespaces_clean(name.split('-')[1])

        if any(e in part2 for e in ['OMENALDIA', 'MEMORIAL']):  # tributes
            return part1
        if any(w in part1 for w in ['BANDERA', 'BANDEIRA', 'IKURRIÑA']):
            return part1

        return name

    @staticmethod
    def __get_race_ids(soup: Tag) -> List[Tuple[int, str]]:
        if not soup.find('table', {'class': 'regatas'}):
            logger.error(f'not races found')
            return []

        rows = soup.find('table', {'class': 'regatas'}).find_all('tr')
        return [(row.find('a')['href'].split('/')[-2], row.find('a')['href'].split('/')[-1]) for row in rows]
