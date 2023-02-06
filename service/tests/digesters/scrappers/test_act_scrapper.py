import datetime
import unittest

import responses

from utils.choices import RACE_TRAINERA, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT
from digesters import ScrappedItem
from digesters.scrappers import ACTScrapper
from tests.utils import add_html_response


class ACTScrapperTest(unittest.TestCase):
    def setUp(self):
        self.scrapper = ACTScrapper()

    @responses.activate
    def test_scrap_act(self):
        add_html_response("https://www.euskolabelliga.com/resultados/index.php?id=es&t=2022", 'euskolabelliga.html')
        add_html_response("https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864858", 'euskolabelliga_details.html')

        self.assertEqual(
            [
                ScrappedItem(
                    league='EUSKO LABEL LIGA',
                    name='XXXIX. BANDERA PETRONOR',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    edition=39,
                    day=1,
                    t_date=datetime.date(2022, 7, 17),
                    club_name='GETARIA',
                    lane=3,
                    series=1,
                    laps=['00:05:03', '00:09:57', '00:15:20', '00:20:09.900000'],
                    trophy_name='BANDERA PETRONOR',
                    participant='GETARIA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864858',
                    datasource='act',
                    town='ZIERBENA',
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='EUSKO LABEL LIGA',
                    name='XXXIX. BANDERA PETRONOR',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    edition=39,
                    day=1,
                    t_date=datetime.date(2022, 7, 17),
                    club_name='ZIERBENA BAHIAS DE BIZKAIA',
                    lane=4,
                    series=2,
                    laps=['00:05:05', '00:09:59', '00:15:26', '00:20:20.980000'],
                    trophy_name='BANDERA PETRONOR',
                    participant='ZIERBENA BAHIAS DE BIZKAIA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864858',
                    datasource='act',
                    town='ZIERBENA',
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='EUSKO LABEL LIGA',
                    name='XXXIX. BANDERA PETRONOR',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    edition=39,
                    day=1,
                    t_date=datetime.date(2022, 7, 17),
                    club_name='Matrix Hondarribia',
                    lane=2,
                    series=3,
                    laps=['00:04:57', '00:09:44', '00:15:05', '00:19:54.520000'],
                    trophy_name='BANDERA PETRONOR',
                    participant='MATRIX HONDARRIBIA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?id=es&r=1647864858',
                    datasource='act',
                    town='ZIERBENA',
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
            ], list(self.scrapper.scrap(2022))
        )
