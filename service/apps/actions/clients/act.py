import datetime
import logging
import re
from typing import List, Optional, Tuple

import requests
from bs4 import Tag, BeautifulSoup
from rest_framework.exceptions import ValidationError

from ai_django.ai_core.utils.strings import whitespaces_clean, find_date, remove_parenthesis, remove_editions
from apps.actions.clients._client import Client
from apps.actions.datasource import Datasource
from apps.entities.models import Entity, League
from apps.entities.services import EntityService, LeagueService
from apps.participants.models import Participant
from apps.participants.normalization import normalize_lap_time
from apps.races.models import Race
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import RACE_TRAINERA, RACE_TIME_TRIAL, RACE_CONVENTIONAL, GENDER_MALE, GENDER_FEMALE, PARTICIPANT_CATEGORY_ABSOLUT

logger = logging.getLogger(__name__)


class ACTClient(Client, source=Datasource.ACT):
    DATASOURCE = Datasource.ACT

    @staticmethod
    def get_race_details_soup(race_id: str, is_female: bool, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if is_female else ''
        url = f'https://www.euskolabelliga.com{female}/resultados/ver.php?r={race_id}'
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_races_summary_soup(year: int, is_female: bool, **kwargs) -> Tuple[Tag, str]:
        female = '/femenina' if is_female else ''
        url = f"https://www.euskolabelliga.com{female}/resultados/index.php?t={year}"
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_race_results_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    def get_web_race_by_id(self, race_id: str, is_female: bool) -> Tuple[Optional[Race], List[Participant]]:
        soup, url = self.get_race_details_soup(race_id, is_female)
        content = soup.find('div', {'class': 'main-content'})
        header = content.find('div', {'class': 'fondo_taula margintaula'}).find('table', {'class', 'taula'})
        series = content.find_all('div', {'class': 'relative'})[1:]
        participant_rows = self.get_participant_rows(series)

        name = whitespaces_clean(content.find('div', {'class': 'relative'}).find('h3').text).upper()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        # parse name, edition, and date from the page title (<edition> <race_name> (<date>))
        edition, t_date, day = self.get_edition(name), find_date(name), self.get_day(name)
        ttype = self.get_type(participant_rows)

        name = self._normalize_race_name(name, is_female=is_female)
        name, edition = self._normalize_edition(name, is_female=is_female, year=t_date.year, edition=edition)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        race = Race(
            creation_date=None,
            laps=self.get_number_of_laps(series[0]),
            lanes=1 if ttype == RACE_TIME_TRIAL else self.get_lanes(participant_rows),
            town=self.get_town(header),
            type=ttype,
            date=t_date,
            day=day,
            cancelled=self.is_cancelled(content),
            cancellation_reasons=None,  # no reason provided by ACT
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=self.get_league(name, is_female),
            modality=RACE_TRAINERA,
            organizer=self.get_organizer(header),
            metadata=Race.MetadataBuilder().race_id(race_id).datasource_name(self.DATASOURCE).values("details_page", url).build(),
        )
        return race, self._find_race_participants(race, series, is_female=is_female)

    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        if not season:
            season = datetime.date.today().year
        self._validate_season_gender(season, is_female)
        soup, _ = self.get_races_summary_soup(year=season, is_female=is_female)

        if not soup.find('div', {'class': 'zutabe_ezkerra'}):
            logger.error(f'{self.DATASOURCE}: no races found for {season=}')
            return []

        table = soup.find('table', {'class': 'taula tablepadding'})
        rows = table.find('tbody').find_all('tr')

        return [row.find('td', {'class': 'race_name'}).find('a')['href'].split('=')[-1] for row in rows]

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################
    def _find_race_participants(self, race: Race, series: List[Tag], is_female: bool) -> List[Participant]:
        for s in series:
            series_number = s.find('span', {'class': 'tanda'}).text
            participants = s.find('tbody').find_all('tr')
            for participant in participants:
                club_name = participant.find('td', {'class': 'club'})
                if not club_name:
                    continue

                yield Participant(
                    race=race,
                    club_name=club_name.text,
                    club=self._find_club(club_name.text),
                    distance=2778 if is_female else 5556,
                    laps=self.get_laps(participant),
                    lane=self.get_lane(participant),
                    series=int(series_number),
                    gender=GENDER_FEMALE if is_female else GENDER_MALE,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                )

    @staticmethod
    def _validate_season_gender(season: int, is_female: bool):
        today = datetime.date.today()
        if is_female:
            if season < 2009 or season > today.year:
                raise ValidationError({'season': f'Should be between {2009} and {today.year}'})
        else:
            if season < 2003 or season > today.year:
                raise ValidationError({'season': f'Should be between {2003} and {today.year}'})

    ####################################################
    #                   SOUP GETTERS                   #
    ####################################################
    @staticmethod
    def get_town(soup: Tag) -> Optional[str]:
        cols = soup.find('tbody').find_all('td')
        return whitespaces_clean(cols[1].text).upper() if len(cols) > 1 else None

    @staticmethod
    def get_organizer(soup: Tag) -> Optional[Entity]:
        cols = soup.find('tbody').find_all('td')
        organizer = whitespaces_clean(cols[0].text).upper() if len(cols) > 0 else None

        if not organizer:
            return None

        try:
            return EntityService.get_closest_by_name_type(organizer, entity_type=None)
        except Entity.DoesNotExist:
            return None

    @staticmethod
    def get_league(name: str, is_female: bool) -> League:
        if is_play_off(name):
            return LeagueService.get_by_name('ACT')

        return LeagueService.get_by_name('LIGA EUSKOTREN') if is_female \
            else LeagueService.get_by_name('EUSKO LABEL LIGA')

    @staticmethod
    def get_day(name: str) -> int:
        if is_play_off(name):  # exception case
            return 1 if '1' in name else 2
        matches = re.findall(r'\(?(\dJ|J\d)\)?', name)
        return int(re.findall(r'\d+', matches[0])[0].strip()) if matches else 1

    @staticmethod
    def get_participant_rows(series: List[Tag]) -> List[Tag]:
        return [p for s in series for p in s.find('tbody').find_all('tr')]

    @staticmethod
    def get_lane(participant_row: Tag) -> str:
        return participant_row.find_all('td', {'class': 'puntua'})[0].text

    def get_type(self, rows: List[Tag]) -> str:
        lanes = list(self.get_lane(p) for p in rows)
        return RACE_TIME_TRIAL if all(int(lane) == int(lanes[0]) for lane in lanes) else RACE_CONVENTIONAL

    def get_lanes(self, rows: List[Tag]) -> int:
        lanes = list(self.get_lane(p) for p in rows)
        return max(int(lane) for lane in lanes)

    @staticmethod
    def get_number_of_laps(series: Tag) -> int:
        return len([col for col in series.find('thead').find_all('th') if 'Cia' in col.text]) + 1

    @staticmethod
    def get_laps(participant: Tag) -> List[datetime.time]:
        return [t for t in [normalize_lap_time(e.text) for e in participant.find_all('td')[2:-1] if e] if t is not None]

    @staticmethod
    def is_cancelled(soup: Tag) -> bool:
        # race_id=1301303104|1301302999
        # try to find the "No puntuable" text in the header
        return soup.find('p').text.upper() == 'NO PUNTUABLE'

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################

    def normalize(self, field: str, value: str, is_female: bool = False, t_date: datetime.date = None, **kwargs):
        if field == 'race_name':
            return self._normalize_race_name(value, is_female)
        if field == 'edition':
            return self._normalize_edition(value, is_female, year=t_date.year, edition=kwargs.pop('edition'))
        return value

    @staticmethod
    def _normalize_race_name(name: str, is_female: bool = False):
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
    def _normalize_edition(name: str, is_female: bool, year: int, edition: int) -> Tuple[str, int]:
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
