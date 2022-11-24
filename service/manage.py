#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from environs import Env


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    if 'test' in sys.argv:
        import logging
        from django.conf import settings
        from config import tests as test_settings

        logger.info('Running Test Settings')
        logging.disable(logging.CRITICAL)

        [setattr(settings, i, getattr(test_settings, i)) for i in dir(test_settings) if not i.startswith("__")]

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    if not os.environ.get('DOCKER', False):
        import logging

        logger = logging.getLogger(__name__)

        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        Env().read_env(env_file, override=True)
        logger.info(f'Using env: {env_file}')

    main()
