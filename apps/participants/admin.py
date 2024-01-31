from django.contrib import admin

from apps.participants.models import Participant, Penalty


class PenaltyInline(admin.TabularInline):
    model = Penalty


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [PenaltyInline]
    list_filter = ('club', 'race__league')


admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Penalty, admin.ModelAdmin)
