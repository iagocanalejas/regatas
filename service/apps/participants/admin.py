from django.contrib import admin

from apps.participants.models import Participant


class ParticipantAdmin(admin.ModelAdmin):
    list_filter = ('club', 'race__league')


admin.site.register(Participant, ParticipantAdmin)
