import os.path

from django.conf import settings
from django.test import TestCase

from apps.races.models import Flag, Trophy
from apps.races.services import FlagService, TrophyService


class CompetitionServiceTest(TestCase):
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

    def test_search_weird_cases(self):
        flag = Flag.objects.get(pk=200)
        query = "BANDEIRA 525 ANIVERSARIO DA ARRIBADA CONCELLO DE BAIONA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        flag = Flag.objects.get(pk=4)
        query = "BANDERA DE ELANTXOBEKO"  # Will return "ELANTXOBEKO ESTROPADA"
        self.assertEqual(flag, FlagService.get_closest_by_name(query))
