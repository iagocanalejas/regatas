from django.contrib import admin
from djutils.admin import TraceableModelAdmin

from apps.entities.models import Entity, League


class EntityAdmin(TraceableModelAdmin):
    list_filter = ("type",)


admin.site.register(Entity, EntityAdmin)
admin.site.register(League, TraceableModelAdmin)
