from typing import Optional

from rest_framework import serializers

from apps.entities.models import League, Entity
from apps.participants.models import Participant
from apps.races.models import Race, Trophy, Flag


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ('id', 'name', 'gender', 'symbol')
        ordering = ('name',)


class EntitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_name(entity) -> str:
        return f'{entity}'

    class Meta:
        model = Entity
        fields = (
            'id',
            'name',
        )
        ordering = ('name',)


class ClubSerializer(EntitySerializer):
    pass


class OrganizerSerializer(serializers.Serializer):
    clubs = ClubSerializer(many=True)
    leagues = EntitySerializer(many=True)
    federations = EntitySerializer(many=True)
    private = EntitySerializer(many=True)

    def update(self, instance, validated_data):
        raise NotImplementedError

    def create(self, validated_data):
        raise NotImplementedError


class TrophySerializer(serializers.ModelSerializer):
    class Meta:
        model = Trophy
        fields = (
            'id',
            'name',
        )
        ordering = ('name',)


class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = (
            'id',
            'name',
        )
        ordering = ('name',)


class SimpleRaceSerializer(serializers.ModelSerializer):
    trophy = TrophySerializer()
    flag = FlagSerializer()
    league = LeagueSerializer(allow_null=True)
    gender = serializers.SerializerMethodField()

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
        )


class SimpleParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ('id', 'laps', 'lane', 'series', 'gender', 'category', 'distance')
