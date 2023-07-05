import json
import logging
from typing import Optional

import inquirer
from django.core.management import BaseCommand
from rest_framework import serializers

from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.participants.models import Participant
from apps.races.models import Race
from apps.serializers import TrophySerializer, FlagSerializer, LeagueSerializer, EntitySerializer
from utils.choices import GENDER_FEMALE
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Tries to find a race in the database or scrapping the pages'

    def add_arguments(self, parser):
        parser.add_argument('datasource', type=str, help='Datasource from where to retrieve.')
        parser.add_argument('race_id', type=str, help='Race to find.')
        parser.add_argument('--female', action='store_true', default=False)

    def handle(self, *args, **options):
        logger.info(f'{options}')

        race_id = options['race_id']
        datasource = options['datasource']
        is_female = options['female']

        if datasource and not Datasource.is_valid(datasource):
            raise ValueError(f'invalid {datasource=}')
        if not datasource:
            raise ValueError(f'unknown datasource')

        client = Client(source=datasource)
        race, participants = client.get_db_race_by_id(race_id, gender=GENDER_FEMALE if is_female else None)

        if race:
            raise StopProcessing(f'{race=} already exists')

        race, participants = client.get_web_race_by_id(race_id, is_female=is_female)

        serialized_race = CommandRaceSerializer(race).data
        print(json.dumps(serialized_race, indent=4))
        if not inquirer.confirm(f"Save new race in the database?", default=False):
            raise StopProcessing

        race.save()
        participants = list(participants)
        for participant in participants:
            participant.race = race

        serialized_participants = CommandParticipantSerializer(participants, many=True).data
        for index, serialized_participant in enumerate(serialized_participants):
            print(json.dumps(serialized_participant, indent=4))
            if not inquirer.confirm(f"Save new participant for {race=} in the database?", default=False):
                continue
            participants[index].save()


# TODO:
# ARC - 479
# ARC - 480
# ARC - 495
# ARC - 482

# ETE - 442
# ETE - 444
# ETE - 445

class CommandRaceSerializer(serializers.ModelSerializer):
    trophy = TrophySerializer()
    flag = FlagSerializer()
    league = LeagueSerializer(allow_null=True)
    gender = serializers.SerializerMethodField()
    organizer = EntitySerializer(allow_null=True)

    @staticmethod
    def get_gender(race: Race) -> Optional[str]:
        if race.league:
            return race.league.gender
        genders = list({p.gender for p in list(race.participants.all())})
        return genders[0] if len(genders) == 1 else None

    class Meta:
        model = Race
        fields = (
            'id',
            'type',
            'modality',
            'gender',
            'day',
            'date',
            'cancelled',
            'trophy',
            'trophy_edition',
            'flag',
            'flag_edition',
            'league',
            'sponsor',
            'laps',
            'lanes',
            'town',
            'organizer'
        )


class CommandParticipantSerializer(serializers.ModelSerializer):
    club = EntitySerializer()
    club_name = serializers.SerializerMethodField()

    @staticmethod
    def get_club_name(participant: Participant) -> Optional[str]:
        extra = None
        if participant.club_name:
            extra = [e for e in ['B', 'C', 'D'] if e in participant.club_name.split()]
            extra = ''.join(e for e in extra) if extra else None
        return f'{participant.club} "{extra}"' if extra else None

    class Meta:
        model = Participant
        fields = ('id', 'laps', 'lane', 'series', 'gender', 'category', 'distance', 'club', 'club_name')
