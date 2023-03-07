from typing import List

from apps.actions.clients import LGTClient
from apps.actions.datasource import Datasource
from apps.actions.digesters import LGTSoupDigester
from apps.actions.management.utils import ScrappedItem
from apps.actions.management.scrappers import Scrapper
from apps.entities.normalization import normalize_club_name
from utils.exceptions import StopProcessing


class LGTScrapper(Scrapper):
    DATASOURCE = Datasource.LGT

    _excluded_ids = [
        1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 15, 23, 25, 26, 27, 28, 31, 32, 33, 34, 36, 37, 40, 41, 44, 50, 51, 54, 55, 56, 57, 58, 59, 75, 88,
        94, 95, 96, 97, 98, 99, 103, 104, 105, 106, 108, 125, 131, 137, 138, 147, 151
    ]  # weird races
    _client: LGTClient = LGTClient(source=DATASOURCE)

    def __init__(self, is_female: bool = False):
        self._is_female = is_female

    def scrap(self, race_id: int, **kwargs) -> List[ScrappedItem]:
        if race_id in self._excluded_ids:
            raise StopProcessing

        soup, _ = self._client.get_race_results_soup(race_id=str(race_id))
        if not soup.find('table', {'id': 'tabla-tempos'}):
            raise StopProcessing
        details_soup, url = self._client.get_race_details_soup(race_id=str(race_id))

        digester = LGTSoupDigester(details_soup=details_soup, results_soup=soup)

        name = digester.get_name()
        edition = digester.get_edition()
        t_date = digester.get_date()
        day = digester.get_day()
        league = digester.get_league()
        town = digester.get_town()
        organizer = digester.get_organizer()

        # known hardcoded mappings too specific to be implemented
        trophy_name = digester.normalize_race_name(name, is_female=any(e in name for e in ['FEMENINA', 'FEMININA']))
        trophy_name, edition = digester.hardcoded_playoff_edition(trophy_name, year=t_date.year, edition=edition)

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
                gender=digester.get_gender(),
                category=digester.get_category(),
                club_name=club_name,
                lane=digester.get_lane(participant),
                series=digester.get_series(participant),
                laps=[t.isoformat() for t in digester.get_laps(participant)],
                distance=digester.get_distance(),
                trophy_name=trophy_name,
                participant=normalize_club_name(club_name),
                race_id=str(race_id),
                url=url,
                datasource=self.DATASOURCE,
            )
