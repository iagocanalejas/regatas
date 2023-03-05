import datetime
import os

import responses
from django.test import TestCase

from apps.actions.clients import LGTClient
from apps.actions.datasource import Datasource
from apps.entities.models import League
from apps.races.models import Race, Flag
from config import settings
from tests.utils import add_html_response
from utils.choices import RACE_CONVENTIONAL, RACE_TRAINERA


class LGTClientTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    def setUp(self):
        self.client = LGTClient(source=Datasource.LGT)

    def test_get_db_race_by_id(self):
        db_race, db_participants = self.client.get_db_race_by_id('11')

        # check client can find local race
        self.assertEqual(db_race, Race.objects.get(pk=2))

    @responses.activate
    def test_get_web_race_by_id(self):
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/principal/regata/11', 'lgt_details.html')

        web_race, web_participants = self.client.get_web_race_by_id('11', is_female=False)

        # check client can parse web result
        self.assertEqual(web_race.flag, Flag.objects.get(pk=2))
        self.assertEqual(web_race.flag_edition, 9)
        self.assertEqual(web_race.league, League.objects.get(pk=5))
        self.assertEqual(web_race.town, 'PEIRAO DE O GROVE')
        self.assertEqual(web_race.type, RACE_CONVENTIONAL)
        self.assertEqual(web_race.modality, RACE_TRAINERA)
        self.assertEqual(web_race.date, datetime.date.fromisoformat('2020-07-25'))
        self.assertEqual(web_race.lanes, 4)
        self.assertEqual(web_race.laps, 4)

        # check client can parse participants
        self.assertEqual(len(list(web_participants)), 3)

    @responses.activate
    def test_get_ids_by_season(self):
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)

        # empty results to halt the processing
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)

        race_ids = self.client.get_ids_by_season(season=2023)

        self.assertEqual(race_ids, ['12', '13', '14'])

    @responses.activate
    def test_get_ids_by_season_will_halt_with_3_invalid_pages(self):
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)

        race_ids = self.client.get_ids_by_season(season=2023)

        self.assertEqual(race_ids, [])
