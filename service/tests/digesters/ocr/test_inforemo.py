import datetime
import locale
import os
import unittest

from django.conf import settings

from digesters import ScrappedItem
from digesters.ocr import ImageOCRInforemo
from digesters.ocr._image import IMAGE_INFOREMO
from utils.choices import GENDER_FEMALE, RACE_TRAINERA, PARTICIPANT_CATEGORY_ABSOLUT, GENDER_MALE, PARTICIPANT_CATEGORY_VETERAN


@unittest.skipIf(os.getenv("CI") == "true", "Skipping in the CI")
class InforemoOCRTest(unittest.TestCase):
    def setUp(self):
        self.original_locale = locale.getlocale()  # ('en_US', 'UTF-8')
        self.digester = ImageOCRInforemo(source=IMAGE_INFOREMO)

    def test_digest_tournament_image(self):
        path = os.path.join(settings.BASE_DIR, 'fixtures', 'img', '20220725_gallego.jpg')
        self.digester.set_language('es_ES.utf8')

        items = list(self.digester.digest(path))

        self.assertIn(
            ScrappedItem(
                league=None,
                name='CAMPEONATO GALEGO DE TRAINERAS',
                gender=GENDER_FEMALE,
                modality=RACE_TRAINERA,
                category=PARTICIPANT_CATEGORY_ABSOLUT,
                distance=5556,
                edition=1,
                day=1,
                t_date=datetime.datetime(2022, 7, 25, 0, 0),
                club_name='CR CABO DA CRUZ',
                lane=1,
                series=1,
                laps=['00:05:08', '00:11:48', '00:17:25', '00:24:13.150000'],
                trophy_name='CAMPEONATO GALEGO DE TRAINERAS',
                participant='CABO DA CRUZ',
                race_id='20220725_gallego.jpg',
                url=None,
                datasource='inforemo',
                town=None,
                organizer=None,
                race_laps=4,
                race_lanes=4,
                cancelled=False,
                disqualified=False
            ), items
        )
        self.assertIn(
            ScrappedItem(
                league=None,
                name='CAMPEONATO GALEGO DE TRAINERAS',
                gender=GENDER_FEMALE,
                modality=RACE_TRAINERA,
                category=PARTICIPANT_CATEGORY_ABSOLUT,
                distance=5556,
                edition=1,
                day=1,
                t_date=datetime.datetime(2022, 7, 25, 0, 0),
                club_name='TIRAN PEREIRA',
                lane=1,
                series=1,
                laps=['00:05:28', '00:12:53', '00:18:49', '00:26:10.420000'],
                trophy_name='CAMPEONATO GALEGO DE TRAINERAS',
                participant='TIRAN PEREIRA',
                race_id='20220725_gallego.jpg',
                url=None,
                datasource='inforemo',
                town=None,
                organizer=None,
                race_laps=4,
                race_lanes=4,
                cancelled=False,
                disqualified=False
            ), items
        )

        self.digester.set_language(self.original_locale)

    def test_digest_memorial_image(self):
        path = os.path.join(settings.BASE_DIR, 'fixtures', 'img', '20230129_lagar.jpg')
        self.digester.set_language('es_ES.utf8')

        items = list(self.digester.digest(path))

        self.assertIn(
            ScrappedItem(
                league=None,
                name='PRETEMPORADA DE TRAINERAS',
                gender=GENDER_MALE,
                modality=RACE_TRAINERA,
                category=PARTICIPANT_CATEGORY_ABSOLUT,
                distance=5556,
                edition=1,
                day=1,
                t_date=datetime.datetime(2023, 1, 29, 0, 0),
                club_name='CR CHAPELA',
                lane=1,
                series=10,
                laps=['00:04:38', '00:11:56', '00:22:13.310000'],
                trophy_name='PRETEMPORADA DE TRAINERAS',
                participant='CHAPELA',
                race_id='20230129_lagar.jpg',
                url=None,
                datasource='inforemo',
                town='Vil MEMORIAL MIGU RNAND LORES LAGAI',
                organizer=None,
                race_laps=3,
                race_lanes=1,
                cancelled=False,
                disqualified=False
            ), items
        )
        self.assertIn(
            ScrappedItem(
                league=None,
                name='PRETEMPORADA DE TRAINERAS',
                gender=GENDER_MALE,
                modality=RACE_TRAINERA,
                category=PARTICIPANT_CATEGORY_VETERAN,
                distance=5556,
                edition=1,
                day=1,
                t_date=datetime.datetime(2023, 1, 29, 0, 0),
                club_name='CR MUROS',
                lane=1,
                series=10,
                laps=['00:05:30', '00:13:43', '00:26:58.280000'],
                trophy_name='PRETEMPORADA DE TRAINERAS',
                participant='MUROS',
                race_id='20230129_lagar.jpg',
                url=None,
                datasource='inforemo',
                town='Vil MEMORIAL MIGU RNAND LORES LAGAI',
                organizer=None,
                race_laps=3,
                race_lanes=1,
                cancelled=False,
                disqualified=False
            ), items
        )

        self.digester.set_language(self.original_locale)
