import os

from django.conf import settings
from django.test import TestCase

from apps.actions.management.commands.recheck import check_race
from apps.actions.management.digester import build_digester
from apps.utils import build_client
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_FEMALE, GENDER_MALE, RACE_CONVENTIONAL, RACE_TRAINERA
from rscraping.data.models import Datasource
from rscraping.data.models import Race as RSRace


class RecheckCommandTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def setUp(self) -> None:
        client = build_client(Datasource.TRAINERAS, GENDER_MALE, category=CATEGORY_ABSOLUT)
        self.digester = build_digester(client=client, force_gender=True, force_category=True)


    def test_invalid_number_of_participants(self):
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
            race_ids=["11"],
            url="test",
            datasource="traineras",
            gender=GENDER_FEMALE,
            category=CATEGORY_ABSOLUT,
            participants=[],
            race_laps=6,
            race_lanes=4,
            cancelled=False,
        )

        with self.assertRaises(AssertionError):
            check_race(self.digester, rs_race, check_participants=True)
