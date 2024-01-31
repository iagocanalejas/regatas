from django.contrib import admin
from django.urls import include, path

from config import settings

# noinspection PyUnresolvedReferences
urlpatterns = [
    path("", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
