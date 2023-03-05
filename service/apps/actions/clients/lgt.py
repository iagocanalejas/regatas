import logging
import re
import time
from datetime import datetime, date
from typing import Tuple, List, Optional

import requests
from bs4 import Tag, BeautifulSoup
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from ai_django.ai_core.utils.strings import remove_editions, remove_parenthesis, whitespaces_clean
from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.entities.models import League
from apps.entities.services import LeagueService
from apps.participants.models import Participant
from apps.participants.normalization import normalize_lap_time
from apps.races.models import Race
from apps.races.normalization import normalize_trophy_name
from utils.checks import is_play_off
from utils.choices import RACE_TRAINERA, RACE_TIME_TRIAL, RACE_CONVENTIONAL, GENDER_FEMALE, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT

logger = logging.getLogger(__name__)


class LGTClient(Client, source=Datasource.LGT):
    DATASOURCE = Datasource.LGT

    @staticmethod
    def get_race_details_soup(race_id: str, **kwargs) -> Tuple[Tag, str]:
        url = f"https://www.ligalgt.com/principal/regata/{race_id}"
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_race_results_soup(race_id: str, **kwargs) -> Tuple[Tag, str]:
        url = 'https://www.ligalgt.com/ajax/principal/ver_resultados.php'
        data = {'liga_id': 1, 'regata_id': race_id}
        response = requests.post(url=url, headers=Client.HEADERS, data=data)

        return BeautifulSoup(response.text, 'html5lib'), url

    @staticmethod
    def get_races_summary_soup(**kwargs) -> Tuple[Tag, str]:
        raise NotImplementedError

    def get_web_race_by_id(self, race_id: str, **kwargs) -> Tuple[Optional[Race], List[Participant]]:
        details_soup, url = self.get_race_details_soup(race_id=race_id)
        results_soup, _ = self.get_race_results_soup(race_id=race_id)

        t_date = datetime.strptime(results_soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[1].text, '%d/%m/%Y').date()
        name = whitespaces_clean(results_soup.find_all('table')[1].find_all('tr')[-1].find_all('td')[0].text).upper()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        # parse name, edition, and date from the page name
        is_female = any(e in name for e in ['FEMENINA', 'FEMININA'])
        edition = self.get_edition(name)
        day = self._normalize_day(name, t_date=t_date)

        name = self._normalize_race_name(name, is_female=is_female)
        name, edition = self._normalize_edition(name, year=t_date.year, edition=edition)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        if not name:
            logger.error(f'{self.DATASOURCE}: no race found for {race_id=}')
            return None, []
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        lanes = self.get_number_of_lanes(results_soup)
        race = Race(
            creation_date=None,
            laps=self.get_number_of_laps(results_soup),
            lanes=lanes,
            town=self.get_town(details_soup),
            type=RACE_TIME_TRIAL if lanes == 1 else RACE_CONVENTIONAL,
            date=t_date,
            day=day,
            cancelled=self.is_cancelled(results_soup),
            cancellation_reasons=None,  # no reason provided by LGT
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=self.get_league(details_soup, name),
            modality=RACE_TRAINERA,
            organizer=self.get_organizer(details_soup),
            metadata=Race.MetadataBuilder().race_id(race_id).datasource_name(self.DATASOURCE).values("details_page", url).build(),
        )

        return race, self._find_race_participants(race, results_soup, is_female)

    def get_ids_by_season(self, season: int = None, is_female: bool = False, **kwargs) -> List[str]:
        today = date.today()
        if season is not None and season != date.today().year:
            logger.error(f'{self.DATASOURCE}: unable to retrieve races for {season=}')
            raise ValidationError({'season': f'should be {today.year}'})
        season = today.year

        # find last found race_id
        races = Race.objects.filter(
            Q(date__year=season) | Q(date__year=(season - 1)),
            league__name__in=[
                'LIGA GALEGA DE TRAIÑAS', 'LIGA GALEGA DE TRAIÑAS A', 'LIGA GALEGA DE TRAIÑAS FEMENINA', 'LIGA GALEGA DE TRAIÑAS B'
            ],
            metadata__datasource__contains=[{
                "datasource_name": 'lgt'
            }]
        )
        last_race_id = 1
        if len(races) > 0:
            last_race_id = max([int(r.metadata['datasource'][0]['race_id']) for r in races if 'race_id' in r.metadata['datasource'][0]])
        logger.info(f'{self.DATASOURCE}: start scrapping from {last_race_id=}')

        # try to load new races
        empty_count = 0
        race_ids = []
        while True:
            last_race_id += 1
            if empty_count > 3:  # stops the scrapper when 3 races are empty in a row
                break

            soup, _ = self.get_race_results_soup(str(last_race_id))
            if soup.find('table', {'id': 'tabla-tempos'}):
                race_ids.append(str(last_race_id))
                empty_count = 0
                time.sleep(1)
            else:
                empty_count += 1

        if not race_ids:
            logger.error(f'{self.DATASOURCE}: no races found for {season=}')
            return []

        return race_ids

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################
    def _find_race_participants(self, race: Race, soup: Tag, is_female: bool) -> List[Participant]:
        series = 1
        for row in soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) == 1:
                series += 1
                continue

            club_name = row.find_all('td')[1].text
            if club_name == 'LIBRE':
                continue

            yield Participant(
                race=race,
                club_name=club_name,
                club=self._find_club(club_name),
                distance=5556,
                laps=self.get_laps(row),
                lane=row.find('td', {
                    'class': 'boiapdf'
                }).text,
                series=series,
                gender=GENDER_FEMALE if is_female else GENDER_MALE,
                category=PARTICIPANT_CATEGORY_ABSOLUT,
            )

    ####################################################
    #                   SOUP GETTERS                   #
    ####################################################

    @staticmethod
    def get_league(soup: Tag, name: str) -> League:
        if is_play_off(name):
            return LeagueService.get_by_name('LGT')

        value = whitespaces_clean(soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[2].find('span').text)
        return LeagueService.get_by_name(value)

    @staticmethod
    def get_town(soup: Tag) -> Optional[str]:
        value = soup.find('div', {'id': 'regata'}).find('div', {'class': 'row'}).find_all('p')[0].text
        return whitespaces_clean(value).upper().replace('PORTO DE ', '')

    def get_organizer(self, soup: Tag) -> Optional[str]:
        organizer = soup.find('div', {'class': 'col-md-2 col-xs-3 txt_center pics100'})
        organizer = whitespaces_clean(organizer.text).upper().replace('ORGANIZA:', '').strip() if organizer else None
        return self._find_club(organizer) if organizer else None

    @staticmethod
    def get_number_of_laps(series: Tag) -> int:
        return len(series.find('table', {'id': 'tabla-tempos'}).find_all('tr')[0].find_all('th')) - 2

    @staticmethod
    def get_number_of_lanes(series: Tag) -> int:
        values = series.find('table', {'id': 'tabla-tempos'}).find_all('td', {'class': 'boiapdf'})
        return max([int(v.text) for v in values if v != 'BOIA'])

    @staticmethod
    def get_laps(soup: Tag) -> List[time]:
        return [t for t in [normalize_lap_time(e.text) for e in soup.find_all('td')[2:] if e] if t is not None]

    @staticmethod
    def is_cancelled(soup: Tag) -> bool:
        # race_id=114
        # assume no final time is set for cancelled races (as in the example)
        times = []
        for row in soup.find('table', {'id': 'tabla-tempos'}).find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) == 1 or row.find_all('td')[1].text == 'LIBRE':
                continue
            times.append(columns[-1].text.strip())
        return all(x == '-' for x in times)

    ####################################################
    #                  NORMALIZATION                   #
    ####################################################

    def normalize(self, field: str, value: str, is_female: bool = False, t_date: date = None, **kwargs):
        if field == 'race_name':
            return self._normalize_race_name(value, is_female)
        if field == 'day':
            return self._normalize_day(value, t_date)
        if field == 'edition':
            return self._normalize_edition(value, t_date.year, kwargs.pop('edition'))
        return value

    @staticmethod
    def _normalize_race_name(name: str, is_female: bool = False) -> Optional[str]:
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
    def _normalize_day(name: str, t_date: date = None) -> int:
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
    def _normalize_edition(name: str, year: int, edition: int) -> Tuple[str, int]:
        if is_play_off(name):
            return name, (year - 2011)
        return name, edition
