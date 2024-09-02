import os.path
from datetime import datetime

from django.conf import settings
from django.test import TestCase

from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from apps.races.models import Race
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_MALE


class ParticipantServiceTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, "fixtures", "test-db.yaml")]

    def test_get_year_speeds_by_club(self):
        club = Entity.objects.get(pk=25)
        participants = [
            Participant(
                club=club,
                race=Race.objects.get(pk=1),
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in ["21:30.21"]],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=club,
                race=Race.objects.get(pk=2),
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in []],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=club,
                race=Race.objects.get(pk=3),
                distance=5556,
                laps=[
                    datetime.strptime(lap, "%M:%S.%f").time()
                    for lap in ["05:12.00", "10:15.00", "15:43.00", "21:38.21"]
                ],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
        ]

        for participant in participants:
            participant.save()

        speeds = ParticipantService.get_year_speeds_filtered_by(
            club=club,
            league=None,
            flag=None,
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            branch_teams=False,
            only_league_races=False,
            normalize=False,
        )

        self.assertEqual(speeds, {2009: [15.407060490983739], 2022: [15.502592601204455]})

    def test_get_year_speeds_by_flag(self):
        race = Race.objects.all().first()
        participants = [
            Participant(
                club=Entity.objects.get(pk=25),
                race=race,
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in ["21:30.21"]],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=Entity.objects.get(pk=23),
                race=race,
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in []],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=Entity.objects.get(pk=24),
                race=race,
                distance=5556,
                laps=[
                    datetime.strptime(lap, "%M:%S.%f").time()
                    for lap in ["05:12.00", "10:15.00", "15:43.00", "21:38.21"]
                ],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
        ]

        for participant in participants:
            participant.save()

        speeds = ParticipantService.get_year_speeds_filtered_by(
            club=None,
            league=None,
            flag=race.flag,  # pyright: ignore
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            branch_teams=False,
            only_league_races=False,
            normalize=False,
        )

        self.assertEqual(speeds, {2009: [15.502592601204455, 15.407060490983739]})

    def test_get_nth_speed_by_year(self):
        club = Entity.objects.get(pk=25)
        participants = [
            Participant(
                club=club,
                race=Race.objects.get(pk=1),
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in ["21:30.21"]],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=club,
                race=Race.objects.get(pk=2),
                distance=5556,
                laps=[
                    datetime.strptime(lap, "%M:%S.%f").time()
                    for lap in ["05:12.00", "10:15.00", "15:43.00", "21:38.21"]
                ],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
            Participant(
                club=club,
                race=Race.objects.get(pk=3),
                distance=5556,
                laps=[datetime.strptime(lap, "%M:%S.%f").time() for lap in []],
                lane=1,
                series=1,
                handicap=None,
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
            ),
        ]

        for participant in participants:
            participant.save()

        speeds = ParticipantService.get_nth_speed_filtered_by(
            index=1,
            club=None,
            league=None,
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            year=2022,
            branch_teams=False,
            only_league_races=False,
            normalize=False,
        )

        self.assertEqual(speeds, [15.502592601204455, 15.407060490983739])
