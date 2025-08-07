from django.contrib import admin
from django.urls import path

# noinspection PyUnresolvedReferences
urlpatterns = [
    path("", admin.site.urls),
]
