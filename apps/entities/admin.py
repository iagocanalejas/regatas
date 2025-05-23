from django.contrib import admin

from apps.entities.models import Entity, EntityPartnership, League
from djutils.admin import TraceableModelAdmin


@admin.register(Entity)
class EntityAdmin(TraceableModelAdmin):
    list_filter = ("type",)


admin.site.register(EntityPartnership, admin.ModelAdmin)
admin.site.register(League, TraceableModelAdmin)
