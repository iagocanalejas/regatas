import datetime
import os

import responses
from django.test import TestCase

from apps.actions.clients import ACTClient
from apps.actions.datasource import Datasource
from apps.entities.models import League
from apps.races.models import Race, Flag
from django.conf import settings
from tests.utils import add_html_response
from utils.choices import RACE_CONVENTIONAL, RACE_TRAINERA


class ACTClientTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    def setUp(self):
        self.client = ACTClient(source=Datasource.ACT)

    def test_get_db_race_by_id(self):
        db_race, db_participants = self.client.get_db_race_by_id('1647864858')

        # check client can find local race
        self.assertEqual(db_race, Race.objects.get(pk=1))

    @responses.activate
    def test_get_web_race_by_id(self):
        add_html_response("https://www.euskolabelliga.com/resultados/ver.php?r=1647864858", 'euskolabelliga_details.html')

        web_race, web_participants = self.client.get_web_race_by_id('1647864858', is_female=False)

        # check client can parse web result
        self.assertEqual(web_race.flag, Flag.objects.get(pk=85))
        self.assertEqual(web_race.flag_edition, 39)
        self.assertEqual(web_race.league, League.objects.get(pk=2))
        self.assertEqual(web_race.town, 'ZIERBENA BIZKAIA')
        self.assertEqual(web_race.type, RACE_CONVENTIONAL)
        self.assertEqual(web_race.modality, RACE_TRAINERA)
        self.assertEqual(web_race.date, datetime.date.fromisoformat('2022-07-17'))
        self.assertEqual(web_race.lanes, 4)
        self.assertEqual(web_race.laps, 4)

        # check client can parse participants
        self.assertEqual(len(list(web_participants)), 3)

    @responses.activate
    def test_get_ids_by_season(self):
        add_html_response("https://www.euskolabelliga.com/resultados/index.php?t=2022", 'euskolabelliga.html')

        race_ids = self.client.get_ids_by_season(season=2022, is_female=False)
        self.assertEqual(race_ids, ['1647864858'])
