#!/usr/bin/env python3

import logging

from django.core.management import BaseCommand

from apps.actions.management.helpers.database import check_continuous_editions, check_values, fill_organizers
from apps.actions.management.helpers.database.checks import check_genders
from apps.races.models import Flag, Trophy

logger = logging.getLogger(__name__)


# TODO: command to find distinct types (CONVENTIONAL|TIME_TRIAL) for the same race
# TODO: command to run throught races and find towns with low levenstein distance


class Command(BaseCommand):
    help = """
    checkeditions: Check for missing continuous editions in trophies and flags.
    Parameters:
        model (str): Specifies which models to check for missing editions.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    fillorganizers: Fill missing organizer_id for trophies and flags.
    Parameters:
        model (str): Specifies which models to process for missing organizer_id.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    checklaps: Check for different number or laps in same race.
    Parameters:
        model (str): Specifies which models to check for different number of laps.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    checklanes: Check for different number or lanes in same race.
    Parameters:
        model (str): Specifies which models to check for different number of lanes.
                     Possible values: "all", "trophy"/"trophies", "flag"/"flags".
                     Defaults to "all".

    checkgenders: Check for different genders in the participants of a race not marked as "ALL".
    """

    def add_arguments(self, parser):
        parser.add_argument("command", type=str, help="Command to execute.")
        parser.add_argument("-m", "--model", help="Wich database model the command will be applied to.", default="all")

    def handle(self, *_, **options):
        logger.info(f"{options}")

        command, model = options["command"], options["model"]

        match command:
            case "checkeditions":
                check_continuous_editions(model=self.get_model(model))
            case "checklaps":
                check_values(model=self.get_model(model), value="laps")
            case "checklanes":
                check_values(model=self.get_model(model), value="lanes")
            case "checkgenders":
                check_genders()
            case "fillorganizers":
                fill_organizers(model=self.get_model(model))
            case _:
                raise NotImplementedError(command)

    @staticmethod
    def get_model(model: str) -> type[Trophy] | type[Flag] | None:
        match model:
            case "all":
                return None
            case "trophy", "trophies":
                return Trophy
            case "flag", "flags":
                return Flag
            case _:
                raise NotImplementedError(model)
