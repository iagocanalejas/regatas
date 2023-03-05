from rest_framework import serializers

from apps.entities.serializers import LeagueSerializer, EntitySerializer, ClubSerializer
from apps.participants.models import Participant
from apps.races.models import Race
from apps.races.serializers import TrophySerializer, FlagSerializer


class ScrapActionSerializer(serializers.Serializer):
    datasource = serializers.CharField(required=False, allow_null=False, max_length=20)
    race_id = serializers.CharField(required=False, allow_null=False, max_length=20)
    is_female = serializers.BooleanField(required=False, allow_null=False, default=False)

    def update(self, instance, validated_data):  # pragma: no cover
        raise NotImplementedError

    def create(self, validated_data):  # pragma: no cover
        raise NotImplementedError


class ScrappedParticipantSerializer(serializers.ModelSerializer):
    club = ClubSerializer()

    class Meta:
        model = Participant
        fields = ('id', 'club', 'laps', 'lane', 'series', 'penalties', 'club_name', 'gender', 'category', 'distance')


class ScrappedRaceSerializer(serializers.ModelSerializer):
    trophy = TrophySerializer()
    flag = FlagSerializer()
    league = LeagueSerializer(allow_null=True)
    organizer = EntitySerializer(allow_null=True)
    participants = serializers.SerializerMethodField()

    def get_participants(self, _):
        return ScrappedParticipantSerializer(self.context.get('participants', []), many=True).data

    class Meta:
        model = Race
        fields = (
            'id', 'type', 'town', 'modality', 'day', 'date', 'race_name', 'cancelled', 'sponsor', 'laps', 'lanes', 'trophy',
            'trophy_edition', 'flag', 'flag_edition', 'league', 'organizer', 'cancelled', 'cancellation_reasons', 'participants'
        )


class ActionScrapSerializer(serializers.Serializer):
    db_race = serializers.SerializerMethodField()
    web_race = serializers.SerializerMethodField()

    def get_db_race(self, value):
        return ScrappedRaceSerializer(value.get('db_race'), context={'participants': self.context.get('db_participants', [])}).data

    def get_web_race(self, value):
        return ScrappedRaceSerializer(value.get('web_race'), context={'participants': self.context.get('web_participants', [])}).data

    def update(self, instance, validated_data):  # pragma: no cover
        raise NotImplementedError

    def create(self, validated_data):  # pragma: no cover
        raise NotImplementedError
