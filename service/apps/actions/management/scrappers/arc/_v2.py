import logging
from datetime import date
from typing import List

from apps.actions.clients import ARCClient
from apps.actions.datasource import Datasource
from apps.actions.digesters import ARCSoupDigester
from apps.actions.management.utils import ScrappedItem
from apps.actions.management.scrappers.arc.arc import ARCScrapper
from apps.entities.normalization import normalize_club_name
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class ARCScrapperV2(ARCScrapper, version=Datasource.ARCVersions.V2):
    DATASOURCE = Datasource.ARCVersions.V2
    _excluded_ids = []
    _client: ARCClient = ARCClient(source=Datasource.ARC)

    def scrap(self) -> List[ScrappedItem]:
        if self._year > date.today().year:
            raise StopProcessing

        race_ids = self._client.get_ids_by_season(season=self._year, is_female=self._is_female)
        if len(race_ids) == 0:
            raise StopProcessing

        for race_id in [r for r in race_ids if r not in self._excluded_ids]:
            details_soup, url = self._client.get_race_details_soup(race_id=race_id, is_female=self._is_female)
            digester = ARCSoupDigester(soup=details_soup)

            name = digester.get_name()
            league = digester.get_league(is_female=self._is_female)
            edition = digester.get_edition()
            t_date = digester.get_date()
            day = digester.get_day()
            town = digester.get_town()
            race_lanes = digester.get_race_lanes()
            race_laps = digester.get_race_laps()

            # known hardcoded mappings too specific to be implemented
            trophy_name = digester.normalize_race_name(name, is_female=self._is_female)
            trophy_name, edition, day = digester.hardcoded_name_edition_day(trophy_name, year=self._year, edition=edition, day=day)

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
                    organizer=digester.get_organizer(),
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
                    datasource=Datasource.ARC,
                    race_laps=race_laps,
                    race_lanes=race_lanes,
                )
