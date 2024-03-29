import io
import os.path
import sys
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from apps.actions.management.ingestor import Ingestor
from apps.entities.models import Entity
from apps.races.models import Race
from rscraping.clients import Client
from rscraping.data.constants import GENDER_MALE, RACE_CONVENTIONAL, RACE_TRAINERA
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace


class RaceIngestionTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "races-db.json")]

    @patch("rscraping.clients.Client")
    def setUp(self, client: Client):
        client.DATASOURCE = Datasource.ABE
        self.ingestor = Ingestor(client, ignored_races=[])

        # Redirect stdout to suppress print statements
        sys.stdout = io.StringIO()

    @patch("inquirer.confirm")
    def test_ingest_existing_race(self, mock_confirm):
        mock_confirm.return_value = True
        original_race = Race.objects.get(pk=15)
        rs_race = RSRace(
            name="XV BANDEIRA CONCELLO DE A POBRA",
            date="22/08/2020",
            day=1,
            modality=RACE_TRAINERA,
            type=RACE_CONVENTIONAL,
            league="LIGA GALEGA DE TRAIÑAS B",
            town="A POBRA DO CARAMIÑAL",
            organizer="CLUB REMO PUEBLA",
            sponsor=None,
            normalized_names=[("BANDEIRA CONCELLO DE A POBRA", 15)],
            race_ids=["1"],
            url="test",
            datasource="test",
            gender=GENDER_MALE,
            participants=[],
            race_laps=6,
            race_lanes=4,
            cancelled=False,
        )

        race, _ = self.ingestor.ingest(rs_race)

        self.assertEqual(original_race.lanes, 3)
        self.assertEqual(race.lanes, 4)

        [d.pop("date", None) for d in race.metadata["datasource"]]  # can't compare dates
        self.assertIn(
            {"values": {"details_page": "test"}, "ref_id": "1", "datasource_name": "abe"},
            race.metadata["datasource"],
        )

    def test_ingest_with_data_filling(self):
        rs_race = RSRace(
            name="XV BANDEIRA CONCELLO DE A POBRA",
            date="22/08/1890",
            day=1,
            modality=RACE_TRAINERA,
            type=RACE_CONVENTIONAL,
            league="LIGA GALEGA DE TRAIÑAS B",
            town=None,
            organizer=None,
            sponsor=None,
            normalized_names=[("BANDEIRA CONCELLO DE A POBRA", 15)],
            race_ids=["1"],
            url="test",
            datasource="test",
            gender=GENDER_MALE,
            participants=[],
            race_laps=6,
            race_lanes=4,
            cancelled=False,
        )

        race, _ = self.ingestor.ingest(rs_race)
        self.assertEqual(race.town, "A POBRA DO CARAMIÑAL")
        self.assertEqual(race.organizer, Entity.objects.get(pk=25))
