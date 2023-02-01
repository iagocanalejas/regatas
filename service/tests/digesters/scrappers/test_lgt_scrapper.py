import datetime
import unittest

import responses

from apps.entities.models import LEAGUE_GENDER_MALE
from apps.races.models import RACE_TRAINERA
from digesters import ScrappedItem
from digesters.scrappers import LGTScrapper
from tests.utils import add_html_response


class LGTScrapperTest(unittest.TestCase):
    def setUp(self):
        self.scrapper = LGTScrapper()

    @responses.activate
    def test_scrap_lgt(self):
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/principal/regata/11', 'lgt_details.html')

        self.assertEqual(
            [
                ScrappedItem(
                    league='LIGA A',
                    name='IX BANDEIRA VIRXE DO CARME',
                    gender=LEAGUE_GENDER_MALE,
                    modality=RACE_TRAINERA,
                    edition=9,
                    day=1,
                    t_date=datetime.date(2020, 7, 25),
                    club_name='CR MUROS',
                    lane=4,
                    series=1,
                    laps=['00:06:35', '00:11:59', '00:19:08', '00:24:24.970000'],
                    trophy_name='BANDEIRA VIRXE DO CARME',
                    participant='MUROS',
                    race_id='11',
                    url='https://www.ligalgt.com/principal/regata/11',
                    datasource='lgt',
                    town='PEIRAO DE O GROVE',
                    organizer='MECOS-ISABEL',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='LIGA A',
                    name='IX BANDEIRA VIRXE DO CARME',
                    gender=LEAGUE_GENDER_MALE,
                    modality=RACE_TRAINERA,
                    edition=9,
                    day=1,
                    t_date=datetime.date(2020, 7, 25),
                    club_name='CR CABO DA CRUZ',
                    lane=2,
                    series=2,
                    laps=['00:06:11', '00:11:22', '00:17:49', '00:22:55.920000'],
                    trophy_name='BANDEIRA VIRXE DO CARME',
                    participant='CABO DA CRUZ',
                    race_id='11',
                    url='https://www.ligalgt.com/principal/regata/11',
                    datasource='lgt',
                    town='PEIRAO DE O GROVE',
                    organizer='MECOS-ISABEL',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                ),
                ScrappedItem(
                    league='LIGA A',
                    name='IX BANDEIRA VIRXE DO CARME',
                    gender=LEAGUE_GENDER_MALE,
                    modality=RACE_TRAINERA,
                    edition=9,
                    day=1,
                    t_date=datetime.date(2020, 7, 25),
                    club_name='SD TIRÁN - PEREIRA',
                    lane=4,
                    series=3,
                    laps=['00:05:59', '00:11:02', '00:17:21', '00:22:31.390000'],
                    trophy_name='BANDEIRA VIRXE DO CARME',
                    participant='TIRÁN - PEREIRA',
                    race_id='11',
                    url='https://www.ligalgt.com/principal/regata/11',
                    datasource='lgt',
                    town='PEIRAO DE O GROVE',
                    organizer='MECOS-ISABEL',
                    race_laps=None,
                    race_lanes=None,
                    cancelled=False,
                    disqualified=False
                )
            ], list(self.scrapper.scrap(11))
        )
