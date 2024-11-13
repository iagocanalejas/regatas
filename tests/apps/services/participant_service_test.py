import os.path
from datetime import datetime

from django.conf import settings
from django.test import TestCase

from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from apps.races.models import Race
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_MALE, RACE_CONVENTIONAL, RACE_TRAINERA
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace


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
            day=1,
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

        assert race is not None
        speeds = ParticipantService.get_year_speeds_filtered_by(
            club=None,
            league=None,
            flag=race.flag,
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            day=1,
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
            day=1,
            branch_teams=False,
            only_league_races=False,
            normalize=False,
        )

        self.assertEqual(speeds, [15.502592601204455, 15.407060490983739])

    def test_is_same_participant(self):
        club = Entity.objects.get(pk=25)
        race = Race.objects.get(pk=1)

        db_participant = Participant(
            club=club,
            race=race,
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            club_names=[f"{club.name} B"],
        )

        participant = RSParticipant(
            club_name=f"{club.name} B",
            participant=f"{club.name} B",
            gender=GENDER_MALE,
            category=CATEGORY_ABSOLUT,
            lane=1,
            series=1,
            handicap=None,
            laps=[],
            distance=5556,
            retired=False,
            absent=False,
            guest=False,
            race=RSRace(
                name="XV BANDEIRA CONCELLO DE A POBRA",
                date="22/08/2020",
                day=1,
                modality=RACE_TRAINERA,
                type=RACE_CONVENTIONAL,
                league="LIGA GALEGA DE TRAIÑAS B",
                town="A POBRA DO CARAMIÑAL",
                organizer="CLUB REMO PUEBLA",
                sponsor=None,
                normalized_names=[("BANDEIRA CONCELLO DE A POBRA", 15)],
                race_ids=["11"],
                url="test",
                datasource="traineras",
                gender=GENDER_MALE,
                category=CATEGORY_ABSOLUT,
                participants=[],
                race_laps=6,
                race_lanes=4,
                cancelled=False,
            ),
        )

        self.assertTrue(ParticipantService.is_same_participant(db_participant, participant))
