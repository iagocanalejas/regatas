from django.test import TestCase
from django.utils import timezone
from jsonschema.exceptions import ValidationError

from apps.races.models import Race, Flag
from apps.schemas import MetadataBuilder


class JSONValidatorsTest(TestCase):
    def setUp(self):
        self.flag = Flag(name='TEST FLAG')
        self.flag.save()

    def test_race_metadata_valid_datasource(self):
        metadata = MetadataBuilder().ref_id(1).datasource_name('arc').values('details_page', 'test')
        race = Race(
            date=timezone.now(),
            flag=self.flag,
            flag_edition=1,
            metadata={'datasource': [metadata.build()]},
        )
        race.save()

    def test_race_metadata_invalid_datasource(self):
        race = Race(
            date=timezone.now(),
            flag=self.flag,
            flag_edition=1,
            metadata={'datasource': [{
                'ref_id': '1',
                'datasource_name': 'arc',
                'key': 'details_page'
            }]},
        )
        with self.assertRaises(ValidationError):
            race.save()
