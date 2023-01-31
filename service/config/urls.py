from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.entities.views import LeaguesView, OrganizersView
from apps.races.views import FlagsView, TrophiesView
from config import settings

# @formatter:off
base_urls = [
    path('leagues/', LeaguesView().as_view(), name='leagues'),
    path('organizers/', OrganizersView().as_view(), name='organizers'),
    path('trophies/', TrophiesView().as_view(), name='trophies'),
    path('flags/', FlagsView().as_view(), name='flags'),
]

api_urls = [
    path('', include(base_urls)),
    path('races/', include('apps.races.urls', namespace='races')),
    path('clubs/', include('apps.entities.urls', namespace='clubs')),
    path('requests/', include('apps.requests.urls', namespace='requests')),
]

# noinspection PyUnresolvedReferences
urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
    path('api/', include(api_urls), name='api'),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
# @formatter:on
