from django.contrib import admin

from apps.places.models import Place, Town

admin.site.register(Town, admin.ModelAdmin)
admin.site.register(Place, admin.ModelAdmin)
