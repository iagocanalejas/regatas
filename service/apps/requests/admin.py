from django.contrib import admin

from ai_django.ai_core.admin import StampedModelAdmin
from apps.requests.models import Request

admin.site.register(Request, StampedModelAdmin)
