from rest_framework import serializers

from apps.entities.models import League, Entity


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ('id', 'name', 'gender')
        ordering = ('name',)


class EntitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_name(entity) -> str:
        return f'{entity}'

    class Meta:
        model = Entity
        fields = ('id', 'name',)
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
