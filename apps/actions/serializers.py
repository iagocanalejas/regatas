from rest_framework import serializers

from apps.entities.models import Entity, League
from apps.participants.models import Participant
from apps.places.models import Place, Town
from apps.races.models import Flag, Race, Trophy


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ("id", "name", "gender", "symbol")
        ordering = ("name",)


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ("id", "name")
        ordering = ("name",)


class TrophySerializer(serializers.ModelSerializer):
    class Meta:
        model = Trophy
        fields = ("id", "name")
        ordering = ("name",)


class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ("id", "name")
        ordering = ("name",)


class TownSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Town
        fields = ("id", "name")
        ordering = ("name",)


class PlaceSerializer(serializers.ModelSerializer):
    town = TownSerialzier()

    class Meta:
        model = Place
        fields = ("id", "name", "town")
        ordering = ("name",)


class RaceSerializer(serializers.ModelSerializer):
    trophy = TrophySerializer(allow_null=True)
    flag = FlagSerializer(allow_null=True)
    league = LeagueSerializer(allow_null=True)
    organizer = EntitySerializer(allow_null=True)
    place = PlaceSerializer(allow_null=True)

    class Meta:
        model = Race
        fields = (
            "id",
            "type",
            "modality",
            "day",
            "date",
            "cancelled",
            "trophy",
            "trophy_edition",
            "flag",
            "flag_edition",
            "league",
            "gender",
            "sponsor",
            "laps",
            "lanes",
            "place",
            "organizer",
            "metadata",
        )


class ParticipantSerializer(serializers.ModelSerializer):
    club = EntitySerializer()
    club_name = serializers.SerializerMethodField()

    # noinspection DuplicatedCode
    @staticmethod
    def get_club_name(participant: Participant) -> str | None:
        extra = None
        if len(participant.club_names) > 0:
            extra = [e for e in ["B", "C", "D"] if any(e in w.split() for w in participant.club_names)]
            extra = "".join(e for e in extra) if extra else None
        return f'{participant.club} "{extra}"' if extra else None

    class Meta:
        model = Participant
        fields = ("id", "laps", "lane", "series", "gender", "category", "distance", "club", "club_name")
