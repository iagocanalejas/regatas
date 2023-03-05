import datetime
import os

import responses
from django.test import TestCase

from apps.actions.clients import ARCClient
from apps.actions.datasource import Datasource
from apps.entities.models import League
from apps.races.models import Race, Flag
from config import settings
from tests.utils import add_html_response
from utils.choices import RACE_TRAINERA, RACE_TIME_TRIAL


class ARCClientV2Test(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    def setUp(self):
        self.client = ARCClient(source=Datasource.ARC)

    def test_get_db_race_by_id(self):
        db_race, db_participants = self.client.get_db_race_by_id('158')

        # check client can find local race
        self.assertEqual(db_race, Race.objects.get(pk=3))

    @responses.activate
    def test_get_web_race_by_id(self):
        add_html_response("https://www.liga-arc.com/es/regata/158/unknown", 'arc_v2_details.html')

        web_race, web_participants = self.client.get_web_race_by_id('158', is_female=False)

        # check client can parse web result
        self.assertEqual(web_race.flag, Flag.objects.get(pk=198))
        self.assertEqual(web_race.flag_edition, 17)
        self.assertEqual(web_race.league, League.objects.get(pk=10))
        self.assertEqual(web_race.town, 'COLINDRES')
        self.assertEqual(web_race.type, RACE_TIME_TRIAL)
        self.assertEqual(web_race.modality, RACE_TRAINERA)
        self.assertEqual(web_race.date, datetime.date.fromisoformat('2009-08-22'))
        self.assertEqual(web_race.lanes, 1)
        self.assertEqual(web_race.laps, 4)

        # check client can parse participants
        self.assertEqual(len(list(web_participants)), 2)

    @responses.activate
    def test_get_ids_by_season(self):
        add_html_response("https://www.liga-arc.com/es/resultados/2009", 'arc_v2.html')

        race_ids = self.client.get_ids_by_season(season=2009, is_female=False)
        self.assertEqual(race_ids, ['29'])
