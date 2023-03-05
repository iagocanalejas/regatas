import logging
import re
from datetime import date, datetime
from typing import List, Optional

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean
from apps.actions.clients import ACTClient
from apps.actions.datasource import Datasource
from apps.actions.management.digesters._item import ScrappedItem
from apps.actions.management.digesters.scrappers import Scrapper
from apps.entities.normalization import normalize_club_name
from apps.participants.normalization import normalize_lap_time
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ACTScrapper(Scrapper):
    DATASOURCE = Datasource.ACT

    _excluded_ids = ['1301302999', '1301303104']
    _client: ACTClient = ACTClient(source=DATASOURCE)

    def __init__(self, is_female: bool = False):
        self._is_female = is_female

    def scrap(self, year: int, **kwargs) -> List[ScrappedItem]:
        if year > date.today().year:
            raise StopProcessing

        soup, summary_url = self._client.get_races_summary_soup(year=year, is_female=self._is_female)
        race_ids = self._client.get_ids_by_season(season=year, is_female=self._is_female)
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
            trophy_name, edition = self._client.normalize('edition', trophy_name, self._is_female, t_date=t_date, edition=edition)
            if trophy_name == 'BANDEIRA CONCELLO MOAÑA - GRAN PREMIO FANDICOSTA' and year == 2009:
                day = 2

            # data retrieved from the details page
            details_soup, url = self._client.get_race_details_soup(race_id=race_id, is_female=self._is_female)
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
                        t_date=t_date,
                        edition=edition,
                        day=day,
                        modality=self.get_modality(),
                        league=league,
                        town=town,
                        organizer=organizer,
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
                    )

                series += 1

    ####################################################
    #                      GETTERS                     #
    ####################################################
    def get_name(self, soup: Tag, **kwargs) -> str:
        return whitespaces_clean(soup.find('td', {'class': 'race_name'}).find('a').text).upper()

    def get_date(self, soup: Tag, **kwargs) -> date:
        return datetime.strptime(soup.find_all('td', {'class': 'place'})[1].text.strip(), '%d-%m-%Y').date()

    def get_day(self, name: str, **kwargs) -> int:
        if self.is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\(?(\dJ|J\d)\)?', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    def get_league(self, trophy: str, **kwargs) -> str:
        if self.is_play_off(trophy):
            return 'ACT'
        return 'LIGA EUSKOTREN' if self._is_female else 'EUSKO LABEL LIGA'

    def get_town(self, soup: Tag, **kwargs) -> Optional[str]:
        return whitespaces_clean(soup.find_all('td', {'class': 'place'})[0].text).upper()

    def get_organizer(self, soup: Tag, **kwargs) -> Optional[str]:
        return None

    def get_club_name(self, soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[1].text

    def get_lane(self, soup: Tag, **kwargs) -> int:
        return int(soup.find_all('td')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [t for t in [normalize_lap_time(e.text) for e in soup.find_all('td')[2:-1] if e] if t is not None]
        return [t.isoformat() for t in times]

    def normalized_name(self, name: str, **kwargs) -> str:
        return self._client.normalize(field='race_name', value=name, is_female=self._is_female)

    def normalized_club_name(self, name: str, **kwargs) -> str:
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

    @staticmethod
    def __get_row_for_race_id(soup: Tag, race_id: str) -> Tag:
        rows = soup.find('table', {'class': 'taula tablepadding'}).find('tbody').find_all('tr')
        for row in rows:
            if row.find('td', {'class': 'race_name'}).find('a')['href'].split('=')[-1] == race_id:
                return row
        raise StopProcessing(f'row for race {race_id} not found')
