import re
from datetime import date, datetime, time
from typing import List, Optional, Tuple

from bs4 import Tag

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_parenthesis, remove_editions
from apps.actions.digesters._digester import SoupDigester
from apps.participants.normalization import normalize_lap_time
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import RACE_CONVENTIONAL, RACE_TIME_TRIAL


class ARCSoupDigester(SoupDigester):
    def get_participants(self, **kwargs) -> List[Tag]:
        participants = []
        for table in self.soup.find_all('table', {'class': 'clasificacion tanda'}):
            participants.extend(table.find('tbody').find_all('tr'))
        return participants

    def get_name(self) -> Optional[str]:
        return whitespaces_clean(self.soup.select_one('div[class*="resultado"]').find('h2').text).upper()

    def get_date(self) -> Optional[date]:
        summary = self.soup.find('div', {'class': 'articulo detalles'}).find('div', {'class': 'grid_5 alpha'})
        text = summary.find_all('li')[0].text.upper().replace('FECHA', '')
        text = text.replace('AGO', 'AUG')  # want to avoid changing the locale
        return datetime.strptime(text.strip(), '%d %b %Y').date()

    def get_day(self) -> int:
        name = self.get_name()
        if is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\d+ª día|\(\d+ª? JORNADA\)', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    def get_league(self, is_female: bool) -> Optional[str]:
        if is_female:
            return 'EMAKUMEZKO TRAINERUEN ELKARTEA'
        text = whitespaces_clean(self.soup.find('h1', {'class': 'seccion'}).find('span').text).upper()
        if is_play_off(text):
            return 'ASOCIACIÓN DE REMO DEL CANTÁBRICO'
        return re.sub(r'TEMPORADA \d+ GRUPO', 'ASOCIACIÓN DE REMO DEL CANTÁBRICO', text)

    def get_type(self) -> str:
        return RACE_TIME_TRIAL if self.get_race_lanes() == 1 else RACE_CONVENTIONAL

    def get_town(self) -> Optional[str]:
        summary = self.soup.find('div', {'class': 'articulo detalles'}).find('div', {'class': 'grid_5 alpha'})
        li = summary.find_all('li')
        if len(li) < 4:
            return None  # no town
        text = remove_parenthesis(li[3].text)
        text = text.replace(' Ver mapaOcultar mapa', '')
        return whitespaces_clean(text).upper()

    def get_organizer(self, **kwargs) -> Optional[str]:
        return None

    def get_race_lanes(self) -> int:
        summary = self.soup.find('div', {'class': 'articulo detalles'}).find('div', {'class': 'grid_5 alpha'})
        text = summary.find_all('li')[2].text.upper()
        if 'CONTRARRELOJ' in text:
            return 1
        return int(re.findall(r'\d+', text)[0])

    def get_race_laps(self) -> int:
        summary = self.soup.find('div', {'class': 'articulo detalles'}).find('div', {'class': 'grid_5 alpha'})
        return int(re.findall(r'\d+', summary.find_all('li')[2].text)[1])

    def is_cancelled(self) -> bool:
        # race_id=260
        # try to find the "NO PUNTUABLE" text in the name
        return 'NO PUNTUABLE' in whitespaces_clean(self.soup.select_one('div[class*="resultado"]').find('h2').text).upper()

    def get_club_name(self, participant: Tag, **kwargs) -> Optional[str]:
        return whitespaces_clean(participant.find_all('td')[0].text).upper()

    def get_lane(self, participant: Tag, **kwargs) -> int:
        return int(participant.find_all('th')[0].text)

    def get_series(self, participant: Tag, **kwargs) -> Optional[int]:
        series = 1
        for table in self.soup.find_all('table', {'class': 'clasificacion tanda'}):
            for p in table.find('tbody').find_all('tr'):
                if p == participant:
                    return series
            series += 1

    def get_laps(self, participant: Tag, **kwargs) -> List[time]:
        times = [e.text for e in participant.find_all('td')[1:] if e.text]
        times = [t for t in [normalize_lap_time(e) for e in times] if t is not None]
        return [t for t in times if t.isoformat() != '00:00:00']

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################

    @staticmethod
    def normalize_race_name(name: str, is_female: bool = False, **kwargs) -> Optional[str]:
        name = name.replace('AYTO', 'AYUNTAMIENTO')
        name = name.replace('IKURRINA', 'IKURRIÑA')
        name = name.replace(' AE ', '')
        name = re.sub(r'EXCMO|ILTMO', '', name)
        name = whitespaces_clean(name)

        # remove edition
        name = remove_editions(remove_parenthesis(whitespaces_clean(name)))
        # remove day
        name = re.sub(r'\d+ª día|\(\d+ª? JORNADA\)', '', name)

        if '-' in name:
            part1, part2 = whitespaces_clean(name.split('-')[0]), whitespaces_clean(name.split('-')[1])

            if any(e in part2 for e in ['OMENALDIA', 'MEMORIAL']):  # tributes
                name = part1
            if any(w in part1 for w in ['BANDERA', 'BANDEIRA', 'IKURRIÑA']):
                name = part1

        name = normalize_trophy_name(name, is_female)

        return name

    @staticmethod
    def hardcoded_name_edition_day(name: str, year: int, edition: int, day: int) -> Tuple[str, int, int]:
        if 'AMBILAMP' in name:
            return 'BANDERA AMBILAMP', edition, day
        if 'BANDERA DE CASTRO' in name or 'BANDERA CIUDAD DE CASTRO' in name:
            return 'BANDERA DE CASTRO', edition, day
        if 'CORREO' in name and 'IKURRIÑA' in name:
            return 'EL CORREO IKURRIÑA', (year - 1986), day
        if 'DONIBANE ZIBURUKO' in name:
            return 'DONIBANE ZIBURUKO ESTROPADAK', int(re.findall(r'\d+', name)[0]), 1
        if 'SAN VICENTE DE LA BARQUERA' in name:
            return 'BANDERA SAN VICENTE DE LA BARQUERA', edition, day

        match = re.match(r'\d+ª? JORNADA|JORNADA \d+', name)
        if match:
            arc = 1 if '1' in name else '2'
            return f'REGATA LIGA ARC {arc}', edition, int(re.findall(r'\d+', match.group(0))[0])

        if is_play_off(name):
            return 'PLAY-OFF ARC', (year - 2005), day

        return name, edition, day
