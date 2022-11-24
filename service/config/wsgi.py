"""
WSGI config for service project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application
from environs import Env


if not os.environ.get('DOCKER', False):
    import logging

    logger = logging.getLogger(__name__)

    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    Env().read_env(env_file, override=True)
    logger.info(f'Using env: {env_file}')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
