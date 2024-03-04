#!/usr/bin/env python3

import logging

from django.core.management import BaseCommand

from apps.actions.management.helpers.database import fill_organizers, missing_editions

logger = logging.getLogger(__name__)


# TODO: command to run throught races and find towns with low levenstein distance
# TODO: command to find missing organizers
# TODO: command to find missing editions
# TODO: command to find distinct types (CONVENTIONAL|TIME_TRIAL) for the same race


class Command(BaseCommand):
    help = """
    missingeditions: Check for missing continuous editions in trophies and flags.

    Parameters:
        model (str): Specifies which models to check for missing editions.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    Returns:
        None

    fillorganizers: Fill missing organizer_id for trophies and flags.

    Parameters:
        model (str): Specifies which models to process for missing organizer_id.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    Returns:
        None
    """

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
