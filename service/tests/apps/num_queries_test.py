import os.path

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient
from service.apps.entities.services import EntityService, LeagueService
from service.apps.races.services import FlagService, TrophyService


class DatabaseQueriesTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def setUp(self):
        self.client = APIClient()

    def test_base_urls(self):
        with self.assertNumQueries(1):
            LeagueService.get_with_parent()
        with self.assertNumQueries(1):
            TrophyService.get()
        with self.assertNumQueries(1):
            FlagService.get()

    def test_clubs_urls(self):
        with self.assertNumQueries(1):
            EntityService.get()
        with self.assertNumQueries(1):
            EntityService.get_club_by_id(26)
