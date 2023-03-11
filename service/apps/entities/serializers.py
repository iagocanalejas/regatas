from apps.serializers import SimpleParticipantSerializer, SimpleRaceSerializer


class ParticipationSerializer(SimpleParticipantSerializer):
    race = SimpleRaceSerializer()

    class Meta(SimpleParticipantSerializer.Meta):
        fields = SimpleParticipantSerializer.Meta.fields + ('race',)
