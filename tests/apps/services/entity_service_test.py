import os.path

from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService
from django.conf import settings
from django.test import TestCase


class EntityServiceTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_search_club(self):
        queries = [
            ("SD TIRÁN PEREIRA", 30),
            ("CM CASTROPOL", 14),
            ("DONOSTIA ARRAUN LAGUNAK", 60),
            ("AMEGROVE CLUB DE REMO", 11),
            ("MUGARDOS - A CABANA FERROL", 233),
            ("PASAJES", 234),
            ("SANTURTZI", 50),
            ("SAN PEDRO", 41),
            ("PASAI DONIBANE KOXTAPE", 46),
            ("VILLAGARCIA", 168),
            ("ORIO B", 51),
            ("BOIRO", 222),
        ]

        for query, entity_id in queries:
            query = normalize_club_name(query)
            entity = Entity.all_objects.get(pk=entity_id)
            self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "SELECCIÓN GUIPUZCOANA"
        query = normalize_club_name(query)
        entity = Entity.all_objects.get(pk=66)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query, include_deleted=True))

    def test_search_no_result(self):
        query = "C.N. SANTA LUCÍA - DOES NOT EXIST"
        self.assertIsNone(EntityService.get_closest_club_by_name(query))

        query = "UR-KIROLAK - DOES NOT EXIST"
        self.assertIsNone(EntityService.get_closest_club_by_name(query))

        query = "RIO MERO - DOES NOT EXIST"
        self.assertIsNone(EntityService.get_closest_club_by_name(query))

        query = "SAN MARTIÑO - DOES NOT EXIST"
        self.assertIsNone(EntityService.get_closest_club_by_name(query))
