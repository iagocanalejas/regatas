import os.path

from django.conf import settings
from django.test import TestCase
from utils.choices import CATEGORY_ABSOLUT, GENDER_MALE

from apps.participants.models import Participant
from apps.participants.services import ParticipantService


class ParticipantServiceTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_will_create_branch_participant(self):
        self._save_participant("CR CHAPELA")
        created, _ = ParticipantService.get_participant_or_create(
            participant=Participant(
                club_name="CR CHAPELA B",
                club_id=17,
                race_id=4,
                distance=5556,
                laps=["00:10:37", "00:26:07.040000"],
                lane=1,
                series=1,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            maybe_branch=True,
        )
        self.assertTrue(created)

    def test_will_create_main_participant_existing_branch(self):
        self._save_participant("CR CHAPELA B")
        created, _ = ParticipantService.get_participant_or_create(
            participant=Participant(
                club_name="CR CHAPELA",
                club_id=17,
                race_id=4,
                distance=5556,
                laps=["00:10:37", "00:26:07.040000"],
                lane=1,
                series=1,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            maybe_branch=True,
        )
        self.assertTrue(created)

    @staticmethod
    def _save_participant(name: str):
        Participant(
            club_name=name,
            club_id=17,
            race_id=4,
            distance=5556,
            laps=["00:10:37", "00:26:07.040000"],
            lane=1,
            series=1,
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
        ).save()
