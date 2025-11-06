import io
import os.path
import sys
from unittest.mock import patch

from apps.actions.management.digester import Digester
from apps.entities.models import Entity
from apps.places.models import Place
from apps.races.models import Race
from django.conf import settings
from django.test import TestCase

from rscraping.clients import Client
from rscraping.data.constants import (
    CATEGORY_ABSOLUT,
    GENDER_ALL,
    GENDER_FEMALE,
    GENDER_MALE,
    RACE_CONVENTIONAL,
    RACE_TRAINERA,
)
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace


class DigestionTest(TestCase):
    """
    This test case is used to test the digestion of races that gave trouble when ingesting the first time.
    """

    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "frozen-db.json")]

    @patch("rscraping.clients.Client")
    def setUp(self, client: Client):
        client.DATASOURCE = Datasource.TRAINERAS
        self.digester = Digester(client)

        # Redirect stdout to suppress print statements
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("inquirer.confirm")
    def test_digest_will_merge_fields(self, mock_confirm):
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
            gender=GENDER_FEMALE,
            category=CATEGORY_ABSOLUT,
            participants=[],
            race_laps=6,
            race_lanes=4,
            cancelled=False,
        )

        race, _, status = self.digester.ingest(rs_race)

        self.assertEqual(original_race.lanes, 3)
        self.assertEqual(race.lanes, 4)
        self.assertEqual(race.gender, GENDER_ALL)
        self.assertEqual(status, Digester.Status.MERGED)

        [d.pop("date", None) for d in race.metadata["datasource"]]  # can't compare dates
        [d.pop("data", None) for d in race.metadata["datasource"]]  # don't want to compare data
        self.assertIn(
            {"values": {"details_page": "test"}, "ref_id": "1", "datasource_name": "traineras"},
            race.metadata["datasource"],
        )

    def test_digest_will_fill_missing_fields(self):
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
            category=CATEGORY_ABSOLUT,
            participants=[],
            race_laps=6,
            race_lanes=4,
            cancelled=False,
        )

        race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(race.place, Place.objects.get(pk=3))
        self.assertEqual(race.organizer, Entity.objects.get(pk=25))
        self.assertEqual(status, Digester.Status.NEW)

    @patch("inquirer.confirm")
    def test_force_gender(self, mock_confirm):
        mock_confirm.return_value = True

        rs_race = RSRace(
            name="BANDERA CONCELLO DE REDONDELA",
            date="16/07/2017",
            day=1,
            modality=RACE_TRAINERA,
            type=RACE_CONVENTIONAL,
            league=None,
            town="REDONDELA",
            organizer=None,
            sponsor=None,
            normalized_names=[("BANDERA CONCELLO DE REDONDELA", 3)],
            race_ids=["3636"],
            url="test",
            datasource=Datasource.TRAINERAS,
            gender=GENDER_FEMALE,
            category=CATEGORY_ABSOLUT,
            participants=[],
            race_laps=2,
            race_lanes=3,
            cancelled=False,
        )

        race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(status, Digester.Status.MERGED)

        self.digester._force_gender = True
        race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(status, Digester.Status.NEW)
        self.assertEqual(race.pk, None)

    @patch("inquirer.confirm")
    def test_digestion_existing_participants(self, mock_confirm):
        mock_confirm.return_value = True

        with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", "_existing_participants.json")) as f:
            rs_race = RSRace.from_json(f.read())
            race = Race.objects.get(pk=2800)

        new_race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(race, new_race)
        self.assertEqual(status, Digester.Status.MERGED)

        for participant in rs_race.participants:
            new_participant, status = self.digester.ingest_participant(new_race, participant, False)
            self.assertIsNotNone(new_participant.pk)
            self.assertEqual(status, Digester.Status.EXISTING)

    @patch("inquirer.confirm")
    def test_digestion_existing_b_participants(self, mock_confirm):
        mock_confirm.return_value = True

        with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", "_existing_b_participants.json")) as f:
            rs_race = RSRace.from_json(f.read())
            race = Race.objects.get(pk=1337)

        new_race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(race, new_race)
        self.assertEqual(status, Digester.Status.MERGED)

        for participant in rs_race.participants:
            new_participant, status = self.digester.ingest_participant(new_race, participant, False)
            self.assertIsNotNone(new_participant.pk)
            self.assertEqual(status, Digester.Status.EXISTING)

    @patch("inquirer.confirm")
    def test_digestion(self, mock_confirm):
        """
        This test will ingest all the races inside fixtures/ingestion that match *.json
        """
        mock_confirm.return_value = True

        for file in os.listdir(os.path.join(settings.BASE_DIR, "fixtures", "ingestion")):
            if not file.endswith(".json") or file.startswith("_"):
                continue

            race_id = int(file.split(".")[0])
            race = Race.objects.get(pk=race_id)
            with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", file)) as f:
                rs_race = RSRace.from_json(f.read())

            new_race, _, status = self.digester.ingest(rs_race)
            self.assertEqual(race, new_race)
            self.assertEqual(status, Digester.Status.MERGED)

    @patch("inquirer.confirm")
    def x_test_given_race(self, mock_confirm):
        mock_confirm.return_value = True

        race_id = 537  # change this
        with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", f"{race_id}.json")) as f:
            rs_race = RSRace.from_json(f.read())
            race = Race.objects.get(pk=race_id)

        new_race, _, status = self.digester.ingest(rs_race)
        self.assertEqual(race, new_race)
        self.assertEqual(status, Digester.Status.MERGED)
