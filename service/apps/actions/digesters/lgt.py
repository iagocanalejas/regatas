import re
from datetime import date, datetime, time
from typing import List, Optional, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_editions, remove_parenthesis
from apps.actions.digesters._digester import SoupDigester
from apps.entities.normalization import normalize_club_name
from apps.participants.normalization import normalize_lap_time
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import GENDER_FEMALE, GENDER_MALE, RACE_TIME_TRIAL, RACE_CONVENTIONAL


class LGTSoupDigester(SoupDigester):
    def __init__(self, details_soup: Tag, results_soup: Tag):
        super().__init__(soup=details_soup)
        self.results_soup = results_soup

    def get_participants(self, **kwargs) -> List[Tag]:
        def is_valid(row: Tag) -> bool:
            return len(row.find_all('td')) > 1 and row.find_all('td')[1].text != 'LIBRE'

        return [p for p in self.results_soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:] if is_valid(p)]

    def get_name(self) -> Optional[str]:
        return whitespaces_clean(self.results_soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[0].text).upper()

    def get_gender(self, **kwargs) -> str:
        return GENDER_FEMALE if any(e in self.get_name() for e in ['FEMENINA', 'FEMININA']) else GENDER_MALE

    def get_date(self) -> Optional[date]:
        return datetime.strptime(self.results_soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[1].text, '%d/%m/%Y').date()

    def get_day(self) -> int:
        name, t_date = self.get_name(), self.get_date()
        if 'XORNADA' in name:
            day = int(re.findall(r' \d+', name)[0].strip())
            return day
        if is_play_off(name):  # exception case
            if '1' in name:
                return 1
            if '2' in name:
                return 2
            return 2 if t_date.isoweekday() == 7 else 1  # 2 for sunday
        return 1

    @staticmethod
    def get_distance(**kwargs) -> int:
        return 5556

    def get_league(self) -> Optional[str]:
        if is_play_off(self.get_name()):
            return 'LGT'
        return whitespaces_clean(self.soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[2].find('span').text)

    def get_type(self) -> str:
        return RACE_TIME_TRIAL if self.get_race_lanes() == 1 else RACE_CONVENTIONAL

    def get_town(self) -> Optional[str]:
        value = self.soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[0].text
        return whitespaces_clean(value).upper().replace('PORTO DE ', '')

    def get_organizer(self) -> Optional[str]:
        organizer = self.soup.find('div', {'class': 'col-md-2 col-xs-3 txt_center pics100'})
        organizer = whitespaces_clean(organizer.text).upper().replace('ORGANIZA:', '').strip() if organizer else None
        return normalize_club_name(organizer) if organizer else None

    def get_race_lanes(self) -> int:
        values = self.results_soup.find('table', {'id': 'tabla-tempos'}).find_all('td', {'class': 'boiapdf'})
        return max([int(v.text) for v in values if v != 'BOIA'])

    def get_race_laps(self) -> int:
        return len(self.results_soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[0].find_all('th')) - 2

    def is_cancelled(self) -> bool:
        # race_id=114
        # assume no final time is set for cancelled races (as in the example)
        times = []
        for row in self.results_soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) == 1 or row.find_all('td')[1].text == 'LIBRE':
                continue
            times.append(columns[-1].text.strip())
        return all(x == '-' for x in times)

    def get_club_name(self, participant: Tag, **kwargs) -> Optional[str]:
        return whitespaces_clean(participant.find_all('td')[1].text).upper()

    def get_lane(self, participant: Tag, **kwargs) -> int:
        return int(participant.find_all('td')[0].text)

    def get_series(self, participant: Tag, **kwargs) -> Optional[int]:
        series = 1
        for row in self.results_soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:]:
            if row == participant:
                return series
            if len(row.find_all('td')) == 1:
                series += 1

    def get_laps(self, participant: Tag, **kwargs) -> List[time]:
        return [t for t in [normalize_lap_time(e.text) for e in participant.find_all('td')[2:] if e] if t is not None]

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################

    @staticmethod
    def normalize_race_name(name: str, is_female: bool = False, **kwargs) -> Optional[str]:
        # remove edition and parenthesis
        name = remove_editions(remove_parenthesis(whitespaces_clean(name)))

        # remove day
        name = re.sub(r'(XORNADA )\d+|\d+( XORNADA)', '', name)

        # remove waste
        if name == 'EREWEWEWERW' or name == 'REGATA' or '?' in name:  # wtf
            return None

        if 'TERESA HERRERA' in name:  # lgt never saves the final
            return 'TROFEO TERESA HERRERA (CLASIFICATORIA)'

        if 'PLAY' in name:
            return 'PLAY-OFF LGT'

        name = normalize_trophy_name(name, is_female)
        # remove gender
        for g in ['FEMENINA', 'FEMININA']:
            name = name.replace(g, '')

        return whitespaces_clean(name)

    @staticmethod
    def hardcoded_playoff_edition(name: str, year: int, edition: int) -> Tuple[str, int]:
        if is_play_off(name):
            return name, (year - 2011)
        return name, edition
