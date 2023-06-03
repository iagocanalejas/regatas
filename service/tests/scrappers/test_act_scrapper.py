import datetime
import unittest

import responses

from apps.actions.management.utils import ScrappedItem
from apps.actions.management.scrappers import ACTScrapper
from tests.utils import add_html_response
from utils.choices import RACE_TRAINERA, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT


class ACTScrapperTest(unittest.TestCase):
    def setUp(self):
        self.scrapper = ACTScrapper()

    @responses.activate
    def test_scrap_act(self):
        add_html_response("https://www.euskolabelliga.com/resultados/index.php?t=2022", 'euskolabelliga.html')
        add_html_response("https://www.euskolabelliga.com/resultados/ver.php?r=1647864858", 'euskolabelliga_details.html')

        self.assertEqual(
            [
                ScrappedItem(
                    name='XXXIX. BANDERA PETRONOR',
                    t_date=datetime.date(2022, 7, 17),
                    edition=39,
                    day=1,
                    modality=RACE_TRAINERA,
                    league='EUSKO LABEL LIGA',
                    town='ZIERBENA BIZKAIA',
                    organizer=None,
                    gender=GENDER_MALE,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    club_name='GETARIA',
                    lane=3,
                    series=1,
                    laps=['00:05:03', '00:09:57', '00:15:20', '00:20:09.900000'],
                    distance=5556,
                    trophy_name='BANDERA PETRONOR',
                    participant='GETARIA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?r=1647864858',
                    datasource='act',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    name='XXXIX. BANDERA PETRONOR',
                    t_date=datetime.date(2022, 7, 17),
                    edition=39,
                    day=1,
                    modality=RACE_TRAINERA,
                    league='EUSKO LABEL LIGA',
                    town='ZIERBENA BIZKAIA',
                    organizer=None,
                    gender=GENDER_MALE,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    club_name='ZIERBENA BAHIAS DE BIZKAIA',
                    lane=4,
                    series=2,
                    laps=['00:05:05', '00:09:59', '00:15:26', '00:20:20.980000'],
                    distance=5556,
                    trophy_name='BANDERA PETRONOR',
                    participant='ZIERBENA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?r=1647864858',
                    datasource='act',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    name='XXXIX. BANDERA PETRONOR',
                    t_date=datetime.date(2022, 7, 17),
                    edition=39,
                    day=1,
                    modality=RACE_TRAINERA,
                    league='EUSKO LABEL LIGA',
                    town='ZIERBENA BIZKAIA',
                    organizer=None,
                    gender=GENDER_MALE,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    club_name='MATRIX HONDARRIBIA',
                    lane=2,
                    series=3,
                    laps=['00:04:57', '00:09:44', '00:15:05', '00:19:54.520000'],
                    distance=5556,
                    trophy_name='BANDERA PETRONOR',
                    participant='HONDARRIBIA',
                    race_id='1647864858',
                    url='https://www.euskolabelliga.com/resultados/ver.php?r=1647864858',
                    datasource='act',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                )
            ], list(self.scrapper.scrap(2022))
        )
