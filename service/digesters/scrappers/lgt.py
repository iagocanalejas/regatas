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


class LGTScrapper(Scrapper):
    _excluded_ids = [
        1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 15, 23, 25, 26, 27, 28, 31, 32, 33, 34, 36, 37, 40, 41, 44, 50, 51, 54, 55, 56, 57, 58, 59, 75, 88,
        94, 95, 96, 97, 98, 99, 103, 104, 105, 106, 108, 125, 131, 137, 138, 147, 151
    ]  # weird races
    DATASOURCE: str = 'lgt'

    def scrap(self, race_id: int, **kwargs) -> List[ScrappedItem]:
        if race_id in self._excluded_ids:
            raise StopProcessing

        soup, _ = self.get_summary_soup(race_id=race_id)
        if not soup.find('table', {'id': 'tabla-tempos'}):
            raise StopProcessing

        details_soup, url = self.get_race_details_soup(race_id=str(race_id))

        name = self.get_name(soup)
        trophy_name = self.normalized_name(name, is_female=any(e in name for e in ['FEMENINA', 'FEMININA']))
        edition = self.get_edition(name)
        t_date = self.get_date(soup)
        day = self.get_day(name, t_date=t_date)

        league = self.get_league(details_soup, trophy=trophy_name)
        town = self.get_town(details_soup)
        organizer = self.get_organizer(details_soup)

        # known hardcoded mappings too specific to be implemented
        trophy_name, edition = self.__hardcoded_mappings(t_date.year, trophy_name, edition)

        series = 1
        for row in soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) == 1:
                series += 1
                continue

            club_name = self.get_club_name(row)
            if club_name == 'LIBRE':
                continue

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
                lane=self.get_lane(row),
                laps=self.get_laps(row),
                race_id=str(race_id),
                url=url,
                datasource=self.DATASOURCE,
            )

    ####################################################
    #                      GETTERS                     #
    ####################################################

    def get_summary_soup(self, race_id: int = None, **kwargs) -> Tuple[Tag, str]:
        url = 'https://www.ligalgt.com/ajax/principal/ver_resultados.php'
        data = {'liga_id': 1, 'regata_id': race_id}
        response = requests.post(url=url, headers=self.HEADERS, data=data)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_race_details_soup(self, race_id: str, **kwargs) -> Tuple[Tag, str]:
        url = f"https://www.ligalgt.com/principal/regata/{race_id}"
        response = requests.get(url=url, headers=self.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_league(self, soup: Tag, trophy: str, **kwargs) -> str:
        if self.is_play_off(trophy):
            return 'LGT'
        value = soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[2].find('span').text
        return whitespaces_clean(value)

    def get_name(self, soup: Tag, **kwargs) -> str:
        return whitespaces_clean(soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[0].text).upper()

    def normalized_name(self, name: str, is_female: bool = False, **kwargs) -> str:
        name = whitespaces_clean(name)

        # remove edition
        edition = int_to_roman(self.get_edition(name))
        name = ' '.join(n for n in re.sub(r'[\'\".:]', ' ', name).split() if n != edition)
        # remove day
        name = re.sub(r'(XORNADA )\d+|\d+( XORNADA)', '', name)

        name = self.__remove_waste_name_parts(name)
        name = normalize_trophy_name(name, is_female)

        return name

    def get_day(self, name: str, t_date: date = None, **kwargs) -> int:
        if self.is_play_off(name):  # exception case
            if '1' in name:
                return 1
            if '2' in name:
                return 2
            return 2 if t_date.isoweekday() == 7 else 1  # 2 for sunday
        if 'XORNADA' in name:
            day = int(re.findall(r' \d+', name)[0].strip())
            return day
        return 1

    def get_date(self, soup: Tag, **kwargs) -> date:
        return datetime.strptime(soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[1].text, '%d/%m/%Y').date()

    def get_town(self, soup: Tag, **kwargs) -> Optional[str]:
        value = soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[0].text
        return whitespaces_clean(value).upper().replace('PORTO DE ', '')

    def get_organizer(self, soup: Tag, **kwargs) -> Optional[str]:
        organizer = soup.find('div', {'class': 'col-md-2 col-xs-3 txt_center pics100'})
        organizer = whitespaces_clean(organizer.text).upper().replace('ORGANIZA:', '').strip() if organizer else None
        return self.normalized_club_name(organizer) if organizer else None

    def get_club_name(self, soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[1].text

    def normalized_club_name(self, name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_lane(self, soup: Tag, **kwargs) -> int:
        return int(soup.find_all('td')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [t for t in [self.normalize_time(e.text) for e in soup.find_all('td')[2:] if e] if t is not None]
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

    def __hardcoded_mappings(self, year: int, name: str, edition: int) -> Tuple[str, int]:
        if self.is_play_off(name):
            return name, (year - 2011)
        return name, edition

    @staticmethod
    def __remove_waste_name_parts(name: str) -> str:
        if name == 'EREWEWEWERW' or name == 'REGATA' or '?' in name:  # wtf
            raise StopProcessing

        if 'TERESA HERRERA' in name:  # lgt never saves the final
            return 'TROFEO TERESA HERRERA (CLASIFICATORIA)'

        if 'PLAY' in name:
            return 'PLAY-OFF LGT'
        return name
