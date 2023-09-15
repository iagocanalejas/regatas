from django.contrib import admin
from djutils.admin import ReadOnlyTabularInline, StampedModelAdmin, YearFilter

from apps.participants.models import Participant
from apps.races.models import Flag, Race, Trophy


class RaceYearFilter(YearFilter):
    model = Race


class RaceInline(ReadOnlyTabularInline):
    model = Race


class ParticipantInline(ReadOnlyTabularInline):
    model = Participant


class TrophyAdmin(StampedModelAdmin):
    inlines = [RaceInline]


class FlagTrophyAdmin(StampedModelAdmin):
    inlines = [RaceInline]


class RaceAdmin(StampedModelAdmin):
    inlines = [ParticipantInline]
    list_filter = ("league", RaceYearFilter)


admin.site.register(Trophy, TrophyAdmin)
admin.site.register(Flag, FlagTrophyAdmin)
admin.site.register(Race, RaceAdmin)
