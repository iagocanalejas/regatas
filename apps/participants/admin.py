from django.contrib import admin

from apps.participants.models import Participant, Penalty


class PenaltyInline(admin.TabularInline):
    model = Penalty


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    inlines = [PenaltyInline]
    list_filter = ('club', 'race__league')


admin.site.register(Penalty, admin.ModelAdmin)
