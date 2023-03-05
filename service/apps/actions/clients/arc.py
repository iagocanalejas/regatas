import logging
import re
from datetime import datetime, date, time
from typing import Tuple, Optional, List

import requests
from bs4 import BeautifulSoup, Tag
from rest_framework.exceptions import ValidationError

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_editions, remove_parenthesis
from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.entities.models import League
from apps.entities.services import LeagueService
from apps.participants.models import Participant
from apps.participants.normalization import normalize_lap_time
from apps.races.models import Race
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import RACE_TIME_TRIAL, RACE_CONVENTIONAL, RACE_TRAINERA, GENDER_FEMALE, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT

logger = logging.getLogger(__name__)


class ARCClient(Client, source=Datasource.ARC):
    DATASOURCE = Datasource.ARC

    @staticmethod
    def get_race_details_soup(race_id: str, race_name: str = 'unknown', is_female: bool = False, **kwargs) -> Tuple[Tag, str]:
        female = 'ligaete' if is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/regata/{race_id}/{race_name}"

        response = requests.get(url=url, headers=Client.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_races_summary_soup(year: int, is_female: bool = False, **kwargs) -> Tuple[Tag, str]:
        female = 'ligaete' if is_female else 'liga-arc'
        url = f"https://www.{female}.com/es/resultados/{year}"

        response = requests.get(url=url, headers=Client.HEADERS)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_race_results_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    def get_web_race_by_id(self, race_id: str, is_female: bool) -> Tuple[Optional[Race], List[Participant]]:
        soup, url = self.get_race_details_soup(race_id=race_id, is_female=is_female)
        details_soup = soup.find('div', {'class': 'articulo detalles'}).find('div', {'class': 'grid_5 alpha'})
        results_soup = soup.find_all('table', {'class': 'clasificacion tanda'})

        name = whitespaces_clean(soup.select_one('div[class*="resultado"]').find('h2').text).upper()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        # parse name, edition, and date from the page name
        day = self.get_day(name)
        edition = self.get_edition(name)

        name = self._normalize_race_name(name, is_female=is_female)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        lanes = self.get_number_of_lanes(details_soup)
        race = Race(
            creation_date=None,
            laps=self.get_number_of_laps(details_soup),
            lanes=lanes,
            town=self.get_town(details_soup),
            type=RACE_TIME_TRIAL if lanes == 1 else RACE_CONVENTIONAL,
            date=self.get_date(details_soup),
            day=day,
            cancelled=self.is_cancelled(soup),
            cancellation_reasons=None,  # no reason provided by ARC
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=self.get_league(soup, is_female=is_female),
            modality=RACE_TRAINERA,
            organizer=None,
            metadata=Race.MetadataBuilder().race_id(race_id).datasource_name(self.DATASOURCE).values("details_page", url).build(),
        )

        return race, self._find_race_participants(race, results_soup, is_female)

    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        if not season:
            season = date.today().year
        self._validate_season_gender(season, is_female)
        soup, _ = self.get_races_summary_soup(year=season, is_female=is_female)

        if not soup.find('table', {'class': 'regatas'}):
            logger.error(f'{self.DATASOURCE}: no races found for {season=}')
            return []

        rows = soup.find('table', {'class': 'regatas'}).find_all('tr')
        return [row.find('a')['href'].split('/')[-2] for row in rows]

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################
    def _find_race_participants(self, race: Race, series: List[Tag], is_female: bool) -> List[Participant]:
        for itx, s in enumerate(series):
            participants = s.find('tbody').find_all('tr')
            for participant in participants:
                club_name = participant.find('td', {'class': 'club'}).find('span').find('a')
                yield Participant(
                    race=race,
                    club_name=club_name.text,
                    club=self._find_club(club_name.text),
                    distance=2778 if is_female else 5556,
                    laps=self.get_laps(participant),
                    lane=int(participant.find('th', {
                        'class': 'calle'
                    }).text),
                    series=itx + 1,
                    gender=GENDER_FEMALE if is_female else GENDER_MALE,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                )

    @staticmethod
    def _validate_season_gender(season: int, is_female: bool):
        today = date.today()
        if is_female:
            if season < 2018 or season > today.year:
                raise ValidationError({'season': f'Should be between {2018} and {today.year}'})
        else:
            if season < 2009 or season > today.year:
                raise ValidationError({'season': f'Should be between {2009} and {today.year}'})

    ####################################################
    #                   SOUP GETTERS                   #
    ####################################################

    @staticmethod
    def get_league(soup: Tag, is_female: bool) -> League:
        if is_female:
            return LeagueService.get_by_name('EMAKUMEZKO TRAINERUEN ELKARTEA')

        name = whitespaces_clean(soup.find('h1', {'class': 'seccion'}).find('span').text).upper()
        name = re.sub(r'TEMPORADA \d+ GRUPO', 'ASOCIACIÓN DE REMO DEL CANTÁBRICO', name)
        if is_play_off(name):
            return LeagueService.get_by_name('ASOCIACIÓN DE REMO DEL CANTÁBRICO')
        return LeagueService.get_by_name(name)

    @staticmethod
    def get_date(soup: Tag) -> date:
        t_date = soup.find('li', {'class': 'fecha'}).text.upper()
        t_date = t_date.replace('FECHA', '').replace('AGO', 'AUG')  # avoid changing the locale
        return datetime.strptime(t_date.strip(), '%d %b %Y').date()

    @staticmethod
    def get_town(soup: Tag) -> Optional[str]:
        li = soup.find_all('li')
        if len(li) < 4:
            return None  # no town
        text = remove_parenthesis(li[3].text)
        text = text.replace(' Ver mapaOcultar mapa', '')
        return whitespaces_clean(text).upper()

    @staticmethod
    def get_day(name: str) -> int:
        if is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\d+ª día|\(\d+ª? JORNADA\)', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    @staticmethod
    def get_number_of_laps(soup: Tag) -> int:
        return int(re.findall(r'\d+', soup.find_all('li')[2].text)[1])

    @staticmethod
    def get_laps(soup: Tag) -> List[time]:
        times = [e.text for e in soup.find_all('td')[1:] if e.text]
        times = [t for t in [normalize_lap_time(e) for e in times] if t is not None]
        return [t for t in times if t.isoformat() != '00:00:00']

    @staticmethod
    def get_number_of_lanes(soup: Tag) -> int:
        text = soup.find_all('li')[2].text.upper()
        if 'CONTRARRELOJ' in text:
            return 1
        return int(re.findall(r'\d+', text)[0])

    @staticmethod
    def is_cancelled(soup: Tag) -> bool:
        # race_id=260
        # try to find the "NO PUNTUABLE" text in the name
        return 'NO PUNTUABLE' in whitespaces_clean(soup.select_one('div[class*="resultado"]').find('h2').text).upper()

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################

    def normalize(self, field: str, value: str, is_female: bool = False, **kwargs):
        if field == 'race_name':
            return self._normalize_race_name(value, is_female)
        if field == 'edition':
            return self._normalize_day_edition(value, year=kwargs.pop('year'), edition=kwargs.pop('edition'), day=kwargs.pop('day'))
        return value

    @staticmethod
    def _normalize_race_name(name: str, is_female: bool):
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
    def _normalize_day_edition(name: str, year: int, edition: int, day: int) -> Tuple[str, int, int]:
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
