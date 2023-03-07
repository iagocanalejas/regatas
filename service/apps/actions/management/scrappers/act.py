import logging
from datetime import date
from typing import List

from ai_django.ai_core.utils.strings import remove_parenthesis
from apps.actions.clients import ACTClient
from apps.actions.datasource import Datasource
from apps.actions.digesters import ACTSoupDigester
from apps.actions.management.utils import ScrappedItem
from apps.actions.management.scrappers import Scrapper
from apps.entities.normalization import normalize_club_name
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

        race_ids = self._client.get_ids_by_season(season=year, is_female=self._is_female)
        if len(race_ids) == 0:
            raise StopProcessing

        for race_id in [r for r in race_ids if r not in self._excluded_ids]:
            details_soup, url = self._client.get_race_details_soup(race_id=race_id, is_female=self._is_female)
            digester = ACTSoupDigester(soup=details_soup)

            name = remove_parenthesis(digester.get_name())
            town = digester.get_town()
            t_date = digester.get_date()
            league = digester.get_league(is_female=self._is_female)
            organizer = digester.get_organizer()
            edition = digester.get_edition()
            day = digester.get_day()

            # name normalization
            trophy_name = digester.normalize_race_name(name, is_female=self._is_female)
            trophy_name, edition = digester.hardcoded_name_edition(trophy_name, self._is_female, year=t_date.year, edition=edition)
            if trophy_name == 'BANDEIRA CONCELLO MOAÑA - GRAN PREMIO FANDICOSTA' and year == 2009:
                day = 2

            for participant in digester.get_participants():
                club_name = digester.get_club_name(participant)
                yield ScrappedItem(
                    name=name,
                    t_date=t_date,
                    edition=edition,
                    day=day,
                    modality=digester.get_modality(),
                    league=league,
                    town=town,
                    organizer=organizer,
                    gender=digester.get_gender(is_female=self._is_female),
                    category=digester.get_category(),
                    club_name=club_name,
                    lane=digester.get_lane(participant),
                    series=digester.get_series(participant),
                    laps=[t.isoformat() for t in digester.get_laps(participant)],
                    distance=digester.get_distance(is_female=self._is_female),
                    trophy_name=trophy_name,
                    participant=normalize_club_name(club_name),
                    race_id=race_id,
                    url=url,
                    datasource=self.DATASOURCE,
                )
