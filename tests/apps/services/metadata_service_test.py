import os.path

from django.conf import settings
from django.test import TestCase

from apps.races.models import Race
from apps.races.services import MetadataService
from apps.schemas import MetadataBuilder
from rscraping.data.constants import CATEGORY_ALL, GENDER_ALL
from rscraping.data.models import Datasource


class MetadataServiceTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_race_exists(self):
        race = Race.objects.get(pk=1)
        race.gender = GENDER_ALL
        race.category = CATEGORY_ALL
        race.metadata = {
            "datasource": [
                (MetadataBuilder().ref_id("1").datasource_name(Datasource.TRAINERAS).values("key", "value").build())
            ]
        }
        race.save()

        self.assertTrue(MetadataService.exists(Datasource.TRAINERAS, ref_id="1"))
