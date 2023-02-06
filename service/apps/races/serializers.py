from typing import Optional

from rest_framework import serializers

from apps.entities.models import League, Entity
from utils.choices import ENTITY_CLUB
from apps.entities.serializers import LeagueSerializer, EntitySerializer, ClubSerializer
from apps.participants.models import Participant, Penalty
from apps.races.models import Trophy, Flag, Race


class RaceParamsSerializer(serializers.Serializer):
    trophy = serializers.PrimaryKeyRelatedField(queryset=Trophy.objects, required=False, allow_null=True)
    flag = serializers.PrimaryKeyRelatedField(queryset=Flag.objects, required=False, allow_null=True)
    league = serializers.PrimaryKeyRelatedField(queryset=League.objects, required=False, allow_null=True)
    participant_club = serializers.PrimaryKeyRelatedField(queryset=Entity.objects.filter(type=ENTITY_CLUB), required=False)

    year = serializers.IntegerField(required=False, allow_null=False)
    keywords = serializers.CharField(required=False, allow_null=False)

    def update(self, instance, validated_data):  # pragma: no cover
        raise NotImplementedError

    def create(self, validated_data):  # pragma: no cover
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
        )


class RaceDetailsSerializer(SimpleRaceSerializer):
    organizer = EntitySerializer(allow_null=True)
    distance = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()

    @staticmethod
    def get_distance(race: Race) -> Optional[int]:
        if not race.participants.count():
            return None

        participants = list(race.participants.all())
        valid_distances = [p.distance for p in participants if p.distance]
        return round(sum(valid_distances) / len(valid_distances))

    @staticmethod
    def get_series(race: Race) -> Optional[int]:
        if not race.participants.count():
            return None

        participants = list(race.participants.all())
        series = [p.series for p in participants if p.series]
        return max(series) if series else None

    class Meta(SimpleRaceSerializer.Meta):
        fields = SimpleRaceSerializer.Meta.fields + ('laps', 'lanes', 'series', 'town', 'organizer', 'distance')


class PenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = Penalty
        fields = ('penalty', 'disqualification', 'reason')


class RaceParticipantSerializer(serializers.ModelSerializer):
    club = ClubSerializer()
    penalties = PenaltySerializer(many=True)
    disqualified = serializers.SerializerMethodField()
    club_name = serializers.SerializerMethodField()

    @staticmethod
    def get_disqualified(participant: Participant) -> bool:
        return participant.penalties.filter(disqualification=True).exists()

    @staticmethod
    def get_club_name(participant: Participant) -> Optional[str]:
        extra = [e for e in ['B', 'C', 'D'] if e in participant.club_name.split()]
        extra = ''.join(e for e in extra) if extra else None
        return f'{participant.club} "{extra}"' if extra else None

    class Meta:
        model = Participant
        fields = ('id', 'club', 'laps', 'lane', 'series', 'disqualified', 'penalties', 'club_name', 'gender', 'category')
