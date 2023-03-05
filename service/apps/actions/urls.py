from django.urls import path, include

from apps.actions import views
from apps.actions.apps import ActionsConfig

app_name = ActionsConfig.name

action_urls = [
    path('scrap/', views.ScrapActionView().as_view(), name='scrap'),
]

# @formatter:off
urlpatterns = [
    path('', include(action_urls)),
]
# @formatter:on
