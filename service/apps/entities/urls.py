from django.urls import path

from apps.entities import views
from apps.entities.apps import EntitiesConfig

app_name = EntitiesConfig.name

# @formatter:off
urlpatterns = [
    path('', views.ClubsView().as_view(), name='clubs'),
    path('<int:club_id>/', views.ClubView().as_view(), name='clubs'),
    path('<int:club_id>/races/', views.ClubRacesView().as_view(), name='club-races'),
]
# @formatter:on
