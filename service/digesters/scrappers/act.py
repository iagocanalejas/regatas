import logging
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import requests
from bs4 import Tag, BeautifulSoup

from ai_django.ai_core.utils.strings import whitespaces_clean, int_to_roman
from apps.entities.normalization import normalize_club_name
from apps.races.normalization import normalize_trophy_name
from digesters._item import ScrappedItem
from digesters.scrappers._scrapper import Scrapper
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ACTScrapper(Scrapper):
    _excluded_ids = ['1301302999', '1301303104']
    DATASOURCE: str = 'act'

    def __init__(self, is_female: bool = False):
        self._is_female = is_female

    def scrap(self, year: int, **kwargs) -> List[ScrappedItem]:
        if year > date.today().year:
            raise StopProcessing

        soup, summary_url = self.get_summary_soup(year=year)

        race_ids = self.__get_race_ids(soup)
        if len(race_ids) == 0:
            raise StopProcessing

        for race_id in [r for r in race_ids if r not in self._excluded_ids]:
            row = self.__get_row_for_race_id(soup, race_id)

            # data retrieved from the summary row
            name = self.get_name(row)
            town = self.get_town(row)
            t_date = self.get_date(row)

            # data parsed from the name
            trophy_name = self.normalized_name(name)
            edition = self.get_edition(name)
            day = self.get_day(name)

            # known hardcoded mappings too specific to be implemented
            trophy_name, edition, town = self.__hardcoded_mappings(year, trophy_name, edition, town)
            if trophy_name == 'BANDEIRA CONCELLO MOAÑA - GRAN PREMIO FANDICOSTA' and year == 2009:
                day = 2

            # data retrieved from the details page
            details_soup, url = self.get_race_details_soup(race_id)
            tables = details_soup.find_all('table', {'class': 'taula tablepadding'})
            organizer = self.get_organizer(details_soup)

            series = 1
            for table in tables:
                results = table.find('tbody').find_all('tr')
                for result in results:
                    club_name = self.get_club_name(result)
                    league = self.get_league(trophy=trophy_name)
                    yield ScrappedItem(
                        name=name,
                        trophy_name=trophy_name,
                        town=town,
                        league=league,
                        gender=None,
                        organizer=organizer,
                        edition=edition,
                        day=day,
                        t_date=t_date,
                        club_name=club_name,
                        participant=self.normalized_club_name(club_name),
                        series=series,
                        lane=self.get_lane(result),
                        laps=self.get_laps(result),
                        race_id=race_id,
                        url=url,
                        datasource=self.DATASOURCE,
                    )

                series += 1

    ####################################################
    #                      GETTERS                     #
    ####################################################

    def get_summary_soup(self, year: int, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if self._is_female else ''
        url = f"https://www.euskolabelliga.com{female}/resultados/index.php?id=es&t={year}"
        response = requests.get(url=url, headers=self.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_race_details_soup(self, race_id: str, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if self._is_female else ''
        url = f"https://www.euskolabelliga.com{female}/resultados/ver.php?id=es&r={race_id}"
        response = requests.get(url=url, headers=self.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_league(self, trophy: str, **kwargs) -> str:
        if self.is_play_off(trophy):
            return 'ACT'
        return 'LIGA EUSKOTREN' if self._is_female else 'EUSKO LABEL LIGA'

    def get_name(self, soup: Tag, **kwargs) -> str:
        return whitespaces_clean(soup.find('td', {'class': 'race_name'}).find('a').text).upper()

    def normalized_name(self, name: str, **kwargs) -> str:
        name = whitespaces_clean(name)

        # remove edition
        edition = int_to_roman(self.get_edition(name))
        name = ' '.join(n for n in re.sub(r'[\'\".:]', ' ', name).split() if n != edition)
        # remove day
        name = re.sub(r'\(?(\dJ|J\d)\)?', '', name)

        name = self.__remove_waste_name_parts(name)
        name = normalize_trophy_name(name, self._is_female)

        return name

    def get_day(self, name: str, **kwargs) -> int:
        if self.is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\(?(\dJ|J\d)\)?', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    def get_date(self, soup: Tag, **kwargs) -> date:
        return datetime.strptime(soup.find_all('td', {'class': 'place'})[1].text.strip(), '%d-%m-%Y').date()

    def get_town(self, soup: Tag, **kwargs) -> Optional[str]:
        return whitespaces_clean(soup.find_all('td', {'class': 'place'})[0].text).upper()

    def get_organizer(self, soup: Tag, **kwargs) -> Optional[str]:
        return None

    def get_club_name(self, soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[1].text

    def normalized_club_name(self, name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_lane(self, soup: Tag, **kwargs) -> int:
        return int(soup.find_all('td')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [t for t in [self.normalize_time(e.text) for e in soup.find_all('td')[2:-1] if e] if t is not None]
        return [t.isoformat() for t in times]

    def get_series(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_lanes(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_laps(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_gender(self, soup: Tag, **kwargs) -> Optional[str]:
        raise NotImplementedError

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def __hardcoded_mappings(self, year: int, name: str, edition: int, town: str) -> Tuple[str, int, str]:
        if 'ASTILLERO' in name:
            name, edition = 'BANDERA AYUNTAMIENTO DE ASTILLERO', (year - 1970)
            town = 'ASTILLERO'

        if 'ORIOKO' in name:
            name = 'ORIOKO ESTROPADAK'

        if 'CORREO IKURRIÑA' in name:
            name, edition = 'EL CORREO IKURRIÑA', (year - 1986)
            town = 'LEKEITIO'

        if 'EL CORTE' in name:
            name, edition = 'GRAN PREMIO EL CORTE INGLÉS', (year - 1970)
            town = 'PORTUGALETE'

        if self.is_play_off(name):
            name, edition = ('PLAY-OFF ACT (FEMENINO)', (year - 2017)) if self._is_female \
                else ('PLAY-OFF ACT', (year - 2002))

        return name, edition, town

    @staticmethod
    def __get_row_for_race_id(soup: Tag, race_id: str) -> Tag:
        rows = soup.find('table', {'class': 'taula tablepadding'}).find('tbody').find_all('tr')
        for row in rows:
            if row.find('td', {'class': 'race_name'}).find('a')['href'].split('=')[-1] == race_id:
                return row
        raise StopProcessing(f'row for race {race_id} not found')

    @staticmethod
    def __remove_waste_name_parts(name: str) -> str:
        if '-' not in name:
            return name
        part1, part2 = whitespaces_clean(name.split('-')[0]), whitespaces_clean(name.split('-')[1])

        if 'OMENALDIA' in part2:  # tributes
            return part1
        if 'BILBAO' in part2:
            return 'BANDERA DE BILBAO' if 'BANDERA DE BILBAO' == part2 else 'GRAN PREMIO VILLA DE BILBAO'

        if any(w in part1 for w in ['BANDERA', 'BANDEIRA', 'IKURRIÑA']):
            return part1

        return name

    @staticmethod
    def __get_race_ids(soup: Tag) -> List[str]:
        if not soup.find('div', {'class': 'zutabe_ezkerra'}):
            logger.error(f'not races found')
            return []

        table = soup.find('table', {'class': 'taula tablepadding'})
        rows = table.find('tbody').find_all('tr')

        return [row.find('td', {'class': 'race_name'}).find('a')['href'].split('=')[-1] for row in rows]
