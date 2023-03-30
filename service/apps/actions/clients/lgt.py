import logging
import time
from datetime import date
from typing import Tuple, List, Optional

import requests
from bs4 import Tag, BeautifulSoup
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.actions.digesters import LGTSoupDigester
from apps.entities.services import LeagueService
from apps.participants.models import Participant
from apps.races.models import Race
from apps.schemas import MetadataBuilder

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

    @staticmethod
    def get_club_page_soup(club_id: str, **kwargs) -> Tuple[Tag, str]:
        url = f'https://www.ligalgt.com/principal/club/{club_id}'
        response = requests.get(url=url, headers=Client.HEADERS)

        return BeautifulSoup(response.text, 'html5lib'), url

    def get_web_race_by_id(self, race_id: str, **kwargs) -> Tuple[Optional[Race], List[Participant]]:
        details_soup, url = self.get_race_details_soup(race_id=race_id)
        results_soup, _ = self.get_race_results_soup(race_id=race_id)
        digester = LGTSoupDigester(details_soup=details_soup, results_soup=results_soup)

        name = digester.get_name()
        logger.info(f'{self.DATASOURCE}: found race {name}')

        # parse name, edition, and date from the page name
        t_date = digester.get_date()
        is_female = any(e in name for e in ['FEMENINA', 'FEMININA'])
        edition = digester.get_edition()

        name = digester.normalize_race_name(name, is_female=is_female)
        name, edition = digester.hardcoded_playoff_edition(name, year=t_date.year, edition=edition)
        logger.info(f'{self.DATASOURCE}: race normalized to {name=}')
        if not name:
            logger.error(f'{self.DATASOURCE}: no race found for {race_id=}')
            return None, []
        trophy, flag = self._find_trophy_or_flag(name)

        if not trophy and not flag:
            raise ValidationError({'name': f"no matching trophy/flag found for {name=}"})

        race = Race(
            creation_date=None,
            laps=digester.get_race_laps(),
            lanes=digester.get_race_lanes(),
            town=digester.get_town(),
            type=digester.get_type(),
            date=t_date,
            day=digester.get_day(),
            cancelled=digester.is_cancelled(),
            cancellation_reasons=None,  # no reason provided by LGT
            race_name=name,
            sponsor=None,
            trophy_edition=edition if trophy else None,
            trophy=trophy,
            flag_edition=edition if flag else None,
            flag=flag,
            league=LeagueService.get_by_name(digester.get_league()),
            modality=digester.get_modality(),
            organizer=self._find_organizer(digester.get_organizer()),
            metadata={'datasource': [
                MetadataBuilder().ref_id(race_id).datasource_name(self.DATASOURCE).values("details_page", url).build()
            ]},
        )

        return race, self._find_race_participants(digester, race, is_female)

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
            last_race_id = max([int(r.metadata['datasource'][0]['ref_id']) for r in races if 'ref_id' in r.metadata['datasource'][0]])
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
