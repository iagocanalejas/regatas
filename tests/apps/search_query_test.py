import os.path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.entities.services import EntityService
from apps.races.models import Flag, Trophy
from apps.races.services import FlagService, TrophyService


class SearchQueryTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_search_teresa_herrera(self):
        trophy = Trophy.objects.get(pk=25)
        flag = Flag.objects.get(pk=39)

        query = "ELIMINATORIA TROFEO TERESA HERRERA"
        self.assertEqual(trophy, TrophyService.get_closest_by_name(query))
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = "ELIMINATORIA BANDERA TERESA HERRERA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))
        self.assertEqual(trophy, TrophyService.get_closest_by_name(query))

    def test_search_deputacion(self):
        flag = Flag.objects.get(pk=133)

        query = "BANDEIRA DEPUTACIÓN DA CORUÑA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = "BANDEIRA DEPUTACION DA CORUNA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = "BANDEIRA MASCULINA DEPUTACIÓN DA CORUÑA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = "BANDEIRA DEPUTACION DA CORUNA DE TRAINERAS"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

    def test_search_town(self):
        flag = Flag.objects.get(pk=3)
        query = "BANDEIRA DE MUROS"  # Will return "BANDEIRA CONCELLO DE MUROS"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        flag = Flag.objects.get(pk=5)
        query = "BANDERA DE SESTAO"  # Will return "BANDERA AYUNTAMIENTO DE SESTAO"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        flag = Flag.objects.get(pk=6)
        query = "BANDERA DE LAREDO"  # Will return "BANDERA VILLA DE LAREDO"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

    def test_elantxobeko(self):
        flag = Flag.objects.get(pk=4)

        query = "BANDERA DE ELANTXOBEKO"  # Will return "ELANTXOBEKO ESTROPADA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

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
        entity = Entity.objects.get(pk=90)
        self.assertEqual(entity, EntityService.get_closest_club_by_name(query))

        query = "SAN JUAN DE TIRAN"
        with self.assertRaises(ObjectDoesNotExist):
            EntityService.get_closest_club_by_name(query)

    def test_search_should_raise(self):
        queries = ["C.N. SANTA LUCÍA", "UR-KIROLAK", "RIO MERO", "SAN MARTIÑO"]
        for query in queries:
            with self.assertRaises(ObjectDoesNotExist):
                EntityService.get_closest_club_by_name(query)
