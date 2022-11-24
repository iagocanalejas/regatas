from django.urls import path

from apps.races import views
from apps.races.apps import RacesConfig

app_name = RacesConfig.name

# @formatter:off
urlpatterns = [
    path('', views.RacesView().as_view(), name='races'),
    path('<int:race_id>/', views.RaceView().as_view(), name='races'),
    path('<int:race_id>/participants/', views.RaceParticipantsView().as_view(), name='participants'),
]
# @formatter:on
