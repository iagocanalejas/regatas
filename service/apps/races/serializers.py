from typing import Optional

from rest_framework import serializers

from apps.participants.models import Participant, Penalty
from apps.races.models import Race
from apps.serializers import ClubSerializer, EntitySerializer, SimpleParticipantSerializer, SimpleRaceSerializer


class PenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = Penalty
        fields = ('penalty', 'disqualification', 'reason')


class ParticipantSerializer(SimpleParticipantSerializer):
    club = ClubSerializer()
    penalties = PenaltySerializer(many=True)
    disqualified = serializers.SerializerMethodField()
    club_name = serializers.SerializerMethodField()

    @staticmethod
    def get_disqualified(participant: Participant) -> bool:
        return any(p.disqualification for p in participant.penalties.all())

    @staticmethod
    def get_club_name(participant: Participant) -> Optional[str]:
        extra = None
        if participant.club_name:
            extra = [e for e in ['B', 'C', 'D'] if e in participant.club_name.split()]
            extra = ''.join(e for e in extra) if extra else None
        return f'{participant.club} "{extra}"' if extra else None

    class Meta(SimpleParticipantSerializer.Meta):
        model = Participant
        fields = SimpleParticipantSerializer.Meta.fields + ('club', 'disqualified', 'penalties', 'club_name')


class RaceDetailsSerializer(SimpleRaceSerializer):
    organizer = EntitySerializer(allow_null=True)
    series = serializers.SerializerMethodField()

    @staticmethod
    def get_series(race: Race) -> Optional[int]:
        if not race.participants.count():
            return None

        participants = list(race.participants.all())
        series = [p.series for p in participants if p.series]
        return max(series) if series else None

    class Meta(SimpleRaceSerializer.Meta):
        fields = SimpleRaceSerializer.Meta.fields + ('series', 'town', 'organizer')
