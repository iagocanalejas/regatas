import os.path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService


class EntityServiceTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_search_club(self):
        query = "SD TIRÁN PEREIRA"
        query = normalize_club_name(query)
        entity = Entity.objects.get(pk=30)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "CM CASTROPOL"
        query = normalize_club_name(query)
        entity = Entity.objects.get(pk=14)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "DONOSTIA ARRAUN LAGUNAK"
        query = normalize_club_name(query)
        entity = Entity.objects.get(pk=60)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "AMEGROVE CLUB DE REMO"
        query = normalize_club_name(query)
        entity = Entity.objects.get(pk=11)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "MUGARDOS - A CABANA FERROL"
        query = normalize_club_name(query)
        entity = Entity.objects.get(pk=233)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "SELECCIÓN GUIPUZCOANA"
        query = normalize_club_name(query)
        entity = Entity.all_objects.get(pk=66)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query, include_deleted=True))

        query = "SAN JUAN DE TIRAN"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)

    def test_search_should_raise(self):
        query = "C.N. SANTA LUCÍA - DOES NOT EXIST"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)

        query = "UR-KIROLAK - DOES NOT EXIST"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)

        query = "RIO MERO - DOES NOT EXIST"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)

        query = "SAN MARTIÑO - DOES NOT EXIST"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)
