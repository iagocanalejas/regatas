import datetime
import unittest

import responses

from apps.actions.management.utils import ScrappedItem
from apps.actions.management.scrappers import ARCScrapper
from tests.utils import add_html_response
from utils.choices import RACE_TRAINERA, GENDER_MALE, PARTICIPANT_CATEGORY_ABSOLUT


class ARCScrapperTest(unittest.TestCase):
    def setUp(self):
        self.scrapper_v1 = ARCScrapper(year=2008)
        self.scrapper_v1._GROUPS = ['1']

        self.scrapper_v2 = ARCScrapper(year=2009)

    @responses.activate
    def test_scrap_arc_v1(self):
        add_html_response("https://www.liga-arc.com/historico/resultados.php?temporada=2008&grupo=1", 'arc_v1.html')
        add_html_response("http://www.liga-arc.com/historico/resultados_detalle.php?id=170", 'arc_v1_details.html')

        self.assertEqual(
            [
                ScrappedItem(
                    league='ASOCIACIÓN DE REMO DEL CANTÁBRICO 1',
                    name='XXI BANDERA DE ELENTXOBE',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    distance=5556,
                    edition=21,
                    day=1,
                    t_date=datetime.date(2008, 7, 6),
                    club_name='CASTRO',
                    lane=1,
                    series=1,
                    laps=['00:05:03', '00:10:11', '00:15:28'],
                    trophy_name='BANDERA DE ELENTXOBE',
                    participant='CASTRO URDIALES',
                    race_id='170',
                    url='http://www.liga-arc.com/historico/resultados_detalle.php?id=170',
                    datasource='arc',
                    town=None,
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='ASOCIACIÓN DE REMO DEL CANTÁBRICO 1',
                    name='XXI BANDERA DE ELENTXOBE',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    distance=5556,
                    edition=21,
                    day=1,
                    t_date=datetime.date(2008, 7, 6),
                    club_name='HONDARRIBIA',
                    lane=4,
                    series=2,
                    laps=['00:04:57', '00:10:24', '00:15:37'],
                    trophy_name='BANDERA DE ELENTXOBE',
                    participant='HONDARRIBIA',
                    race_id='170',
                    url='http://www.liga-arc.com/historico/resultados_detalle.php?id=170',
                    datasource='arc',
                    town=None,
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='ASOCIACIÓN DE REMO DEL CANTÁBRICO 1',
                    name='XXI BANDERA DE ELENTXOBE',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    distance=5556,
                    edition=21,
                    day=1,
                    t_date=datetime.date(2008, 7, 6),
                    club_name='KAIKU',
                    lane=4,
                    series=3,
                    laps=['00:04:47', '00:09:58', '00:15:05'],
                    trophy_name='BANDERA DE ELENTXOBE',
                    participant='KAIKU',
                    race_id='170',
                    url='http://www.liga-arc.com/historico/resultados_detalle.php?id=170',
                    datasource='arc',
                    town=None,
                    organizer=None,
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                )
            ], list(self.scrapper_v1.scrap())
        )

    @responses.activate
    def test_scrap_arc_v2(self):
        add_html_response("https://www.liga-arc.com/es/resultados/2009", 'arc_v2.html')
        add_html_response("https://www.liga-arc.com/es/regata/29/unknown", 'arc_v2_details.html')

        self.assertEqual(
            [
                ScrappedItem(
                    league='ASOCIACIÓN DE REMO DEL CANTÁBRICO 2',
                    name='XVII BANDERA RIA DEL ASON',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    distance=5556,
                    edition=17,
                    day=1,
                    t_date=datetime.date(2009, 8, 22),
                    club_name='ZUMAIAKO A.E.',
                    lane=6,
                    series=1,
                    laps=['00:05:48', '00:10:39', '00:16:47', '00:21:37.110000'],
                    trophy_name='BANDERA RIA DEL ASON',
                    participant='ZUMAIAKO A.E.',
                    race_id='29',
                    url='https://www.liga-arc.com/es/regata/29/unknown',
                    datasource='arc',
                    town='COLINDRES',
                    organizer=None,
                    race_laps=4,
                    race_lanes=1,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='ASOCIACIÓN DE REMO DEL CANTÁBRICO 2',
                    name='XVII BANDERA RIA DEL ASON',
                    gender=GENDER_MALE,
                    modality=RACE_TRAINERA,
                    category=PARTICIPANT_CATEGORY_ABSOLUT,
                    distance=5556,
                    edition=17,
                    day=1,
                    t_date=datetime.date(2009, 8, 22),
                    club_name='SANTOÑA EXCELENTE',
                    lane=3,
                    series=2,
                    laps=['00:05:23', '00:10:18', '00:15:58', '00:20:50.020000'],
                    trophy_name='BANDERA RIA DEL ASON',
                    participant='SANTOÑA EXCELENTE',
                    race_id='29',
                    url='https://www.liga-arc.com/es/regata/29/unknown',
                    datasource='arc',
                    town='COLINDRES',
                    organizer=None,
                    race_laps=4,
                    race_lanes=1,
                    cancelled=False,
                    disqualified=False
                )
            ], list(self.scrapper_v2.scrap())
        )
