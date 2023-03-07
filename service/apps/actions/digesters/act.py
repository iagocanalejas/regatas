import re
from datetime import date, time
from typing import List, Optional, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean, find_date, remove_editions, remove_parenthesis
from apps.actions.digesters._digester import SoupDigester
from apps.participants.normalization import normalize_lap_time
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import RACE_TIME_TRIAL, RACE_CONVENTIONAL


class ACTSoupDigester(SoupDigester):
    def get_participants(self, **kwargs) -> List[Tag]:
        participants = []
        for table in self.soup.find_all('table', {'class': 'taula tablepadding'}):
            participants.extend(table.find('tbody').find_all('tr'))
        return participants

    def get_name(self) -> Optional[str]:
        return whitespaces_clean(self.soup.find_all('div', {'class': 'relative'})[0].find('h3').text).upper()

    def get_date(self) -> Optional[date]:
        return find_date(self.get_name())

    def get_day(self) -> int:
        name = self.get_name()
        if is_play_off(name):
            return 1 if '1' in name else 2

        matches = re.findall(r'\(?(\dJ|J\d)\)?', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    def get_league(self, is_female: bool) -> Optional[str]:
        return 'ACT' if is_play_off(self.get_name()) else 'LIGA EUSKOTREN' if is_female else 'EUSKO LABEL LIGA'

    def get_type(self) -> str:
        lanes = list(self.get_lane(p) for p in self.get_participants())
        return RACE_TIME_TRIAL if all(int(lane) == int(lanes[0]) for lane in lanes) else RACE_CONVENTIONAL

    def get_town(self, **kwargs) -> Optional[str]:
        return whitespaces_clean(self.soup.find('div', {'class': 'fondo_taula margintaula'}).find_all('td')[1].text).upper()

    def get_organizer(self) -> Optional[str]:
        content = self.soup.find('div', {'class': 'main-content'})
        cols = content.find('div', {'class': 'fondo_taula margintaula'}).find('table', {'class', 'taula'}).find('tbody').find_all('td')
        organizer = whitespaces_clean(cols[0].text).upper() if len(cols) > 0 else None
        return organizer if organizer else None

    def get_race_lanes(self, **kwargs) -> int:
        if self.get_type() == RACE_TIME_TRIAL:
            return 1
        lanes = list(self.get_lane(p) for p in self.get_participants())
        return max(int(lane) for lane in lanes)

    def get_race_laps(self) -> int:
        columns = self.soup.find_all('table', {'class': 'taula tablepadding'})[0].find('thead').find_all('th')
        return len([col for col in columns if 'Cia' in col.text]) + 1

    def is_cancelled(self) -> bool:
        # race_id=1301303104|1301302999
        # try to find the "No puntuable" text in the header
        return self.soup.find('div', {'class': 'main-content'}).find('p').text.upper() == 'NO PUNTUABLE'

    def get_club_name(self, participant: Tag, **kwargs) -> Optional[str]:
        return whitespaces_clean(participant.find_all('td')[1].text).upper()

    def get_lane(self, participant: Tag, **kwargs) -> int:
        return int(participant.find_all('td')[0].text)

    def get_series(self, participant: Tag, **kwargs) -> int:
        series = 1
        for table in self.soup.find_all('table', {'class': 'taula tablepadding'}):
            for p in table.find('tbody').find_all('tr'):
                if p == participant:
                    return series
            series += 1

    def get_laps(self, participant: Tag, **kwargs) -> List[time]:
        return [t for t in [normalize_lap_time(e.text) for e in participant.find_all('td')[2:-1] if e] if t is not None]

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################
    @staticmethod
    def normalize_race_name(name: str, is_female: bool = False, **kwargs) -> str:
        # remove edition and parenthesis
        name = remove_editions(remove_parenthesis(whitespaces_clean(name)))

        # remove day
        name = re.sub(r'\(?(\dJ|J\d)\)?', '', name)

        # remove waste
        if '-' in name:
            part1, part2 = whitespaces_clean(name.split('-')[0]), whitespaces_clean(name.split('-')[1])

            if 'OMENALDIA' in part2:  # tributes
                name = part1
            elif 'BILBAO' in part2:
                name = 'BANDERA DE BILBAO' if 'BANDERA DE BILBAO' == part2 else 'GRAN PREMIO VILLA DE BILBAO'
            elif any(w in part1 for w in ['BANDERA', 'BANDEIRA', 'IKURRIÑA']):
                name = part1

        return normalize_trophy_name(name, is_female)

    @staticmethod
    def hardcoded_name_edition(name: str, is_female: bool, year: int, edition: int) -> Tuple[str, int]:
        if 'ASTILLERO' in name:
            name, edition = 'BANDERA AYUNTAMIENTO DE ASTILLERO', (year - 1970)

        if 'ORIOKO' in name:
            name = 'ORIOKO ESTROPADAK'

        if 'CORREO IKURRIÑA' in name:
            name, edition = 'EL CORREO IKURRIÑA', (year - 1986)

        if 'EL CORTE' in name:
            name, edition = 'GRAN PREMIO EL CORTE INGLÉS', (year - 1970)

        if is_play_off(name):
            name, edition = ('PLAY-OFF ACT (FEMENINO)', (year - 2017)) if is_female else ('PLAY-OFF ACT', (year - 2002))

        return name, edition
