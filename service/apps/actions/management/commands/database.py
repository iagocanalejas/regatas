import logging

from django.core.management import BaseCommand

from apps.actions.management.helpers.database import missing_editions, missing_towns

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument("command", type=str, help="Command to execute.")

    def handle(self, *_, **options):
        logger.info(f"{options}")

        command = options["command"]

        match command:
            case "missingeditions":
                missing_editions()
            case "missingtowns":
                missing_towns()
            case _:
                raise NotImplementedError(command)
