from datetime import date, datetime
from typing import List, Optional

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean
from apps.actions.clients import LGTClient
from apps.actions.datasource import Datasource
from apps.actions.management.digesters._item import ScrappedItem
from apps.actions.management.digesters.scrappers import Scrapper
from apps.entities.normalization import normalize_club_name
from apps.participants.normalization import normalize_lap_time
from utils.choices import GENDER_FEMALE, GENDER_MALE
from utils.exceptions import StopProcessing


class LGTScrapper(Scrapper):
    DATASOURCE = Datasource.LGT

    _excluded_ids = [
        1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 15, 23, 25, 26, 27, 28, 31, 32, 33, 34, 36, 37, 40, 41, 44, 50, 51, 54, 55, 56, 57, 58, 59, 75, 88,
        94, 95, 96, 97, 98, 99, 103, 104, 105, 106, 108, 125, 131, 137, 138, 147, 151
    ]  # weird races
    _client: LGTClient = LGTClient(source=DATASOURCE)

    def scrap(self, race_id: int, **kwargs) -> List[ScrappedItem]:
        if race_id in self._excluded_ids:
            raise StopProcessing

        soup, _ = self._client.get_race_results_soup(race_id=str(race_id))
        if not soup.find('table', {'id': 'tabla-tempos'}):
            raise StopProcessing

        details_soup, url = self._client.get_race_details_soup(race_id=str(race_id))

        name = self.get_name(soup)
        trophy_name = self.normalized_name(name, is_female=any(e in name for e in ['FEMENINA', 'FEMININA']))
        edition = self.get_edition(name)
        t_date = self.get_date(soup)
        day = self.get_day(name, t_date=t_date)

        league = self.get_league(details_soup, trophy=trophy_name)
        town = self.get_town(details_soup)
        organizer = self.get_organizer(details_soup)

        # known hardcoded mappings too specific to be implemented
        trophy_name, edition = self._client.normalize('edition', trophy_name, t_date=t_date, edition=edition)

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
                t_date=t_date,
                edition=edition,
                day=day,
                modality=self.get_modality(),
                league=league,
                town=town,
                organizer=organizer,
                gender=self.get_gender(name=name),
                category=self.get_category(),
                club_name=club_name,
                lane=self.get_lane(row),
                series=series,
                laps=self.get_laps(row),
                distance=self.get_distance(),
                trophy_name=trophy_name,
                participant=self.normalized_club_name(club_name),
                race_id=str(race_id),
                url=url,
                datasource=self.DATASOURCE,
            )

    ####################################################
    #                      GETTERS                     #
    ####################################################
    def get_name(self, soup: Tag, **kwargs) -> str:
        return whitespaces_clean(soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[0].text).upper()

    def get_date(self, soup: Tag, **kwargs) -> date:
        return datetime.strptime(soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[1].text, '%d/%m/%Y').date()

    def get_day(self, name: str, t_date: date = None, **kwargs) -> int:
        return self._client.normalize(field='day', value=name, t_date=t_date)

    def get_league(self, soup: Tag, trophy: str, **kwargs) -> str:
        if self.is_play_off(trophy):
            return 'LGT'
        value = soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[2].find('span').text
        return whitespaces_clean(value)

    def get_town(self, soup: Tag, **kwargs) -> Optional[str]:
        value = soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[0].text
        return whitespaces_clean(value).upper().replace('PORTO DE ', '')

    def get_organizer(self, soup: Tag, **kwargs) -> Optional[str]:
        organizer = soup.find('div', {'class': 'col-md-2 col-xs-3 txt_center pics100'})
        organizer = whitespaces_clean(organizer.text).upper().replace('ORGANIZA:', '').strip() if organizer else None
        return self.normalized_club_name(organizer) if organizer else None

    def get_gender(self, name: str, **kwargs) -> str:
        return GENDER_FEMALE if any(e in name for e in ['FEMENINA', 'FEMININA']) else GENDER_MALE

    def get_distance(self, **kwargs) -> int:
        return 5556

    def get_club_name(self, soup: Tag, **kwargs) -> str:
        return soup.find_all('td')[1].text

    def get_lane(self, soup: Tag, **kwargs) -> int:
        return int(soup.find_all('td')[0].text)

    def get_laps(self, soup: Tag, **kwargs) -> List[str]:
        times = [t for t in [normalize_lap_time(e.text) for e in soup.find_all('td')[2:] if e] if t is not None]
        return [t.isoformat() for t in times]

    def normalized_name(self, name: str, is_female: bool = False, **kwargs) -> str:
        return self._client.normalize(field='race_name', value=name, is_female=is_female)

    def normalized_club_name(self, name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_series(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_lanes(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError

    def get_race_laps(self, soup: Tag, **kwargs) -> int:
        raise NotImplementedError
