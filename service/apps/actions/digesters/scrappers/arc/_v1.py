import logging
import re
import time
from datetime import date, datetime
from typing import List, Optional, Tuple

import requests
from bs4 import Tag, BeautifulSoup

from ai_django.ai_core.utils.strings import whitespaces_clean, int_to_roman
from apps.entities.normalization import normalize_club_name
from apps.races.normalization import normalize_trophy_name
from apps.actions.digesters._item import ScrappedItem
from apps.actions.digesters.scrappers.arc.arc import ARCScrapper, ARC_V1
from utils.choices import GENDER_MALE
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ARCScrapperV1(ARCScrapper, version=ARC_V1):
    _GROUPS = ['1', '2', 'playoff', 'playoffact']

    _excluded_ids = ['164', '167', '199']

    def scrap(self) -> List[ScrappedItem]:
        if self._year > 2008:
            raise StopProcessing

        for group in self._GROUPS:
            soup, summary_url = self.get_summary_soup(group=group)

            race_ids = self.__get_race_ids(soup)
            if len(race_ids) == 0:
                continue

            for race_id in [r for r in race_ids if r not in self._excluded_ids]:
                # data retrieved from the summary
                name = self.get_name(soup, race_id=race_id)
                t_date = self.get_date(soup, race_id=race_id)
                league = self.get_league(group=group)

                # data parsed from the name
                trophy_name = self.normalized_name(name)
                edition = self.get_edition(name)
                day = self.get_day(name)

                # known hardcoded mappings too specific to be implemented
                trophy_name, edition, day = self.__hardcoded_mappings(trophy_name, edition, day)

                details_soup, url = self.get_race_details_soup(race_id)
                tables = details_soup.find_all('table', {'class': 'resultados'})

                series = 1
                for table in tables:
                    rows = table.find('tbody').find_all('tr')[1:]
                    for row in rows:
                        club_name = self.get_club_name(row)
                        if not club_name:
                            continue

                        yield ScrappedItem(
                            name=name,
                            t_date=t_date,
                            edition=edition,
                            day=day,
                            modality=self.get_modality(),
                            league=league,
                            town=self.get_town(),
                            organizer=self.get_organizer(),
                            gender=self.get_gender(),
                            category=self.get_category(),
                            club_name=club_name,
                            lane=self.get_lane(row),
                            series=series,
                            laps=self.get_laps(row),
                            distance=self.get_distance(),
                            trophy_name=trophy_name,
                            participant=self.normalized_club_name(club_name),
                            race_id=race_id,
                            url=url,
                            datasource=self.DATASOURCE,
                        )

                    series += 1

            time.sleep(1)
        return []

    ####################################################
    #                      GETTERS                     #
    ####################################################

    def get_summary_soup(self, group: str = None) -> Tuple[Tag, str]:
        url = f'https://www.liga-arc.com/historico/resultados.php?temporada={self._year}&grupo={group}'

        response = requests.get(url=url, headers=self.HEADERS)
        return BeautifulSoup(response.text, 'html5lib'), url

    def get_race_details_soup(self, race_id: str, **kwargs) -> Tuple[Tag, str]:
        # noinspection HttpUrlsUsage
        url = f'http://www.liga-arc.com/historico/resultados_detalle.php?id={race_id}'

        response = requests.get(url=url, headers=self.HEADERS)
        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_name(soup: Tag, race_id: str = None, **kwargs) -> str:
        rows = [row.find('a') for row in soup.find_all('div', {'class': 'listado_regatas_nombre'})]
        return whitespaces_clean([row for row in rows if row['href'].split('=')[-1] == race_id][-1].text).upper()

    @staticmethod
    def get_date(soup: Tag, race_id: str = None, **kwargs) -> date:
        rows = [row.find('a') for row in soup.find_all('div', {'class': 'listado_regatas_nombre'})]
        row = [row for row in rows if row['href'].split('=')[-1] == race_id][-1]
        return datetime.strptime(row.previous_element.find_previous_sibling('div').text.strip(), '%d-%m-%Y').date()

    def get_edition(self, name: str) -> int:
        edition = super(ARCScrapperV1, self).get_edition(name)
        if edition != 1 or self.is_play_off(name) or 'ORDENACION GRUPOS' in name:  # already valid edition
            return edition
        if name[0].isdigit():
            return int(name[0])
        return 1

    def get_day(self, name: str, **kwargs) -> int:
        if self.is_play_off(name) or 'ORDENACION GRUPOS' in name:  # exception case
            return 1 if 'PRIMER' in name or name[0] == '1' else 2
        matches = re.findall(r'\(?(\dJ|J\d)\)?', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    @staticmethod
    def get_league(group: str, **kwargs) -> Optional[str]:
        if group == 'playoffact':
            return 'ASOCIACIÓN DE CLUBES DE TRAINERAS'
        elif group == 'playoff':
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO'
        elif group == '1':
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO 1'
        elif group == '2':
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO 2'
        else:
            return None

    def get_town(self, **kwargs) -> Optional[str]:
        return None

    def get_organizer(self, **kwargs) -> Optional[str]:
        return None

    def get_gender(self, **kwargs) -> str:
        return GENDER_MALE  # no female races previous 2009

    @staticmethod
    def get_club_name(soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[1].text.strip().upper()

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [e.text for e in soup.find_all('td')[2:-1] if e.text]
        times = ['21:53.20' if t == '21:63.20' else t for t in times]  # page error
        times = ['17:08,00' if t == '147:08,00' else t for t in times]  # page error

        times = [t for t in [self.normalize_time(e) for e in times] if t is not None]
        return [t.isoformat() for t in times if t.isoformat() != '00:00:00']

    @staticmethod
    def get_lane(soup: Tag, **kwargs) -> int:
        return int(soup.find_all('td')[0].text.strip())

    def normalized_name(self, name: str, **kwargs) -> str:
        name = name.replace('G1 G2', '')
        name = whitespaces_clean(name)

        # remove edition
        edition = int_to_roman(self.get_edition(name))
        name = ' '.join(n for n in re.sub(r'[\'\".:ª]', ' ', name).split() if n != edition)

        if name[0].isdigit():
            name = name[1:].strip()

        name = normalize_trophy_name(name, self._is_female)

        return name

    @staticmethod
    def normalized_club_name(name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_series(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_lanes(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_laps(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def __hardcoded_mappings(self, name: str, edition: int, day: int) -> Tuple[str, int, int]:
        if 'DONIBANE ZIBURUKO' in name:
            return 'DONIBANE ZIBURUKO ESTROPADAK', int(re.findall(r'\d+', name)[0]), 1
        if 'AMBILAMP' in name:
            return 'BANDERA AMBILAMP', edition, day
        if 'BANDERA DE CASTRO' in name:
            return 'BANDERA DE CASTRO', edition, day

        if name == 'PORTUGALETE 2 REGATA (ARC 2)':
            return 'REGATA PORTUGALETE (ARC 2)', 2, 1
        if name == 'IKURRIÑA ILTMO AYTO DE SANTURTZI':
            return 'IKURRIÑA DE SANTURTZI', edition, day

        if self.is_play_off(name):
            if any(e in name for e in ['ACT', 'SAN MIGUEL']):
                return 'PREVIO PLAY-OFF ACT (ARC - ALN)', (self._year - 2005), day
            return 'PLAY-OFF ARC', (self._year - 2005), day
        return name, edition, day

    @staticmethod
    def __get_race_ids(soup: Tag) -> List[str]:
        if not soup.find('div', {'class': 'listado_regatas_nombre'}):
            logger.error(f'not races found')
            return []

        rows = soup.find_all('div', {'class': 'listado_regatas_nombre'})
        return [row.find('a')['href'].split('=')[-1] for row in rows]
