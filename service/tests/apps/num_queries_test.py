import os.path

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient


class DatabaseQueriesTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    def setUp(self):
        self.client = APIClient()

    def test_base_urls(self):
        with self.assertNumQueries(1):
            self.client.get('/api/leagues/')
        with self.assertNumQueries(1):
            self.client.get('/api/organizers/')
        with self.assertNumQueries(1):
            self.client.get('/api/trophies/')
        with self.assertNumQueries(1):
            self.client.get('/api/flags/')

    def test_races_urls(self):
        with self.assertNumQueries(3):
            # count, race & participants
            self.client.get('/api/races/')
        with self.assertNumQueries(2):
            # loads participants in a second query
            self.client.get('/api/races/1/')
        with self.assertNumQueries(2):
            # loads penalties in a second query
            self.client.get('/api/races/1/participants/')

    def test_clubs_urls(self):
        with self.assertNumQueries(1):
            self.client.get('/api/clubs/')
        with self.assertNumQueries(1):
            self.client.get('/api/clubs/26/')
        with self.assertNumQueries(3):
            # count, participation, race__participants
            self.client.get('/api/clubs/26/races/')
