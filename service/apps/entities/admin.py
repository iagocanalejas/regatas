from ai_django.ai_core.admin import TraceableModelAdmin
from django.contrib import admin

from apps.entities.models import Entity, League


class EntityAdmin(TraceableModelAdmin):
    list_filter = ('type',)


admin.site.register(Entity, EntityAdmin)
admin.site.register(League, TraceableModelAdmin)
