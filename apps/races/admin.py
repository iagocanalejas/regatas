from django.contrib import admin

from apps.participants.models import Participant
from apps.races.models import Flag, Race, Trophy
from djutils.admin import ReadOnlyTabularInline, StampedModelAdmin, YearFilter


class RaceYearFilter(YearFilter):
    @property
    def model(self):
        return Race


class RaceInline(ReadOnlyTabularInline):
    model = Race


class ParticipantInline(ReadOnlyTabularInline):
    model = Participant


@admin.register(Trophy)
class TrophyAdmin(StampedModelAdmin):
    inlines = [RaceInline]


@admin.register(Flag)
class FlagTrophyAdmin(StampedModelAdmin):
    inlines = [RaceInline]


@admin.register(Race)
class RaceAdmin(StampedModelAdmin):
    inlines = [ParticipantInline]
    list_filter = ("league", RaceYearFilter)
