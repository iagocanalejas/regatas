from django.urls import path

from apps.requests import views
from apps.requests.apps import RequestsConfig

app_name = RequestsConfig.name

# @formatter:off
urlpatterns = [
    path('', views.RequestsView().as_view(), name='requests'),
]
# @formatter:on
