import os

from django.conf import settings
from django.test import TestCase

from apps.actions.management.commands.scrape import ScrapeConfig
from apps.entities.models import Entity
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_MALE
from rscraping.data.models import Datasource


class ScrapeConfigTests(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def setUp(self):
        self.valid_options = {
            "input_source": Datasource.TRAINERAS.value,
            "race_ids": [],
            "year": "2023",
            "club": None,
            "entity": None,
            "flag": None,
            "sheet_id": "sheet_id",
            "sheet_name": "sheet_name",
            "file_path": "file_path",
            "category": "ABSOLUT",
            "gender": "MALE",
            "table": None,
            "start_year": None,
            "force_gender": False,
            "ignore": [],
            "output": None,
        }

    def test_valid_scrape_config_creation(self):
        config = ScrapeConfig.from_args(**self.valid_options)
        self.assertIsInstance(config, ScrapeConfig)
        self.assertEqual(config.tabular_config.sheet_id, "sheet_id")
        self.assertEqual(config.year, 2023)
        self.assertEqual(config.category, CATEGORY_ABSOLUT)
        self.assertEqual(config.gender, GENDER_MALE)

    def test_invalid_datasource_raises_value_error(self):
        options = self.valid_options.copy()
        options["input_source"] = "INVALID_SOURCE"
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)

    def test_invalid_gender_raises_value_error(self):
        options = self.valid_options.copy()
        options["gender"] = "INVALID_GENDER"
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)

    def test_only_one_of_year_race_ids_flag(self):
        options = self.valid_options.copy()
        options["race_ids"] = ["race1"]
        options["flag"] = "flag1"
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)

    def test_invalid_year_format_raises_value_error(self):
        options = self.valid_options.copy()
        options["year"] = "invalid_year"
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)

    def test_valid_year_parsing(self):
        self.assertEqual(ScrapeConfig.parse_year("all"), ScrapeConfig.ALL_YEARS)
        self.assertEqual(ScrapeConfig.parse_year("2023"), 2023)
        with self.assertRaises(ValueError):
            ScrapeConfig.parse_year("1900")  # Year out of range
        with self.assertRaises(ValueError):
            ScrapeConfig.parse_year("2200")  # Year out of range

    def test_club_requires_year(self):
        options = self.valid_options.copy()
        options["club"] = "some_club"
        options["year"] = None
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)

    def test_entity_id_validation(self):
        options = self.valid_options.copy()
        options["entity"] = "invalid_entity"
        with self.assertRaises(ValueError):
            ScrapeConfig.from_args(**options)
        options["entity"] = "1"
        config = ScrapeConfig.from_args(**options)
        self.assertEqual(config.entity, Entity.objects.get(pk=1))
