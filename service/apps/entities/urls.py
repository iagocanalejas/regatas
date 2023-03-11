from django.urls import path

from apps.entities.apps import EntitiesConfig
from apps.entities import views

app_name = EntitiesConfig.name

# @formatter:off
urlpatterns = [
    path('', views.ClubsView().as_view(), name='clubs'),
    path('<int:club_id>/', views.ClubView().as_view(), name='clubs'),
    path('<int:club_id>/races/', views.ClubRacesView().as_view(), name='club-races'),
]
# @formatter:on
