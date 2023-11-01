#!/usr/bin/env python3

import logging

from django.core.management import BaseCommand

from apps.actions.management.helpers.database import fill_organizers, missing_editions

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument("command", type=str, help="Command to execute.")
        parser.add_argument("-m", "--model", help="Wich database model the command will be applied to.", default="all")

    def handle(self, *_, **options):
        logger.info(f"{options}")

        command, model = options["command"], options["model"]

        match command:
            case "missingeditions":
                missing_editions(model=model)
            case "fillorganizers":
                fill_organizers(model=model)
            case _:
                raise NotImplementedError(command)
