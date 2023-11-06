#!/usr/bin/env python3

import json
import logging

import inquirer
import pandas as pd
from django.core.management import BaseCommand
from django.db.models import Q
from service.apps.races.services import RaceService
from utils.choices import GENDER_ALL
from utils.exceptions import StopProcessing

from apps.actions.management.helpers.races import input_flag, input_trophy
from apps.actions.serializers import RaceSerializer
from apps.entities.models import Entity, League
from apps.participants.models import Participant
from apps.races.models import Race, Trophy
from apps.races.services import FlagService, TrophyService
from pyutils.strings import remove_genders, remove_parenthesis, roman_to_int
from rscraping.data.constants import (
    GENDER_FEMALE,
    GENDER_MALE,
    PARTICIPANT_CATEGORY_ABSOLUT,
    RACE_CONVENTIONAL,
    RACE_TIME_TRIAL,
    RACE_TRAINERA,
)
from rscraping.data.normalization.races import is_play_off

logger = logging.getLogger(__name__)


COLUMN_NAME = "Nome"
COLUMN_DATE = "Fecha"
COLUMN_LEAGUE = "Liga"
COLUMN_EDITION = "Edición"
COLUMN_DISTANCE = "Distancia"
COLUMN_TIME = "Tiempo"
COLUMN_LANE = "Boya"
COLUMN_NUMBER_LANES = "N Boyas"
COLUMN_NUMBER_LAPS = "N Largos"


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Path of the file.")
        parser.add_argument("entity", type=int, help="Entity we are adding data for.")
        parser.add_argument("--female", action="store_true", default=False)

    def handle(self, *_, **options):
        logger.info(f"{options}")

        path, is_female = options["path"], options["female"]
        dfs = _import_file(path)

        while True:
            not_found_races, unmatched_races = _load_races_and_check_errors(dfs, is_female)
            errors = {
                "races_not_found": not_found_races,
                "races_unmatched": unmatched_races,
            }

            ignored_errors = []
            errors = {k: v for k, v in errors.items() if k not in ignored_errors}
            if not any(len(errors[k]) > 0 for k in errors.keys()):
                # if no errors break out of the loop
                break

            print(json.dumps(errors, indent=4, skipkeys=True, ensure_ascii=False))
            _input_races(dfs)
            _create_missing_races(dfs, is_female)
            if not inquirer.confirm("Errors where found. Did you manually fix them?", default=False):
                raise StopProcessing("errors where not fixed")

        entity = Entity.objects.get(pk=options["entity"])
        _update_existing_races(dfs, entity, is_female)


def _import_file(file_path: str) -> pd.DataFrame:
    df_types = {
        "N": int,
        "Club": str,
        "Temp.": int,
        COLUMN_DATE: lambda x: pd.to_datetime(x, format="%d/%m/%Y").date() if x and x != "-" else None,
        COLUMN_LEAGUE: str,
        COLUMN_EDITION: lambda x: roman_to_int(x) if x and x != "-" else None,
        COLUMN_NAME: str,
        "Organizador": str,
        COLUMN_DISTANCE: int,
        COLUMN_TIME: lambda x: pd.to_datetime(x, format="%M:%S.%f").time() if x and x != "-" else None,
        "Puesto": int,
        "Tipo": str,
        COLUMN_NUMBER_LAPS: int,
        COLUMN_NUMBER_LANES: int,
        COLUMN_LANE: int,
    }
    dfs = pd.read_excel(
        file_path,
        header=0,
        index_col=0,
        converters=df_types,
    ).fillna("")

    dfs = dfs[dfs.index.notnull()]
    dfs.drop("AVG", axis=1, inplace=True)
    dfs.drop("MEDIAN", axis=1, inplace=True)
    dfs.drop("Image URL", axis=1, inplace=True)
    assert isinstance(dfs, pd.DataFrame)

    dfs.loc[dfs[COLUMN_LEAGUE] == "Liga A", COLUMN_LEAGUE] = League.objects.get(symbol="LGT A")
    dfs.loc[dfs[COLUMN_LEAGUE] == "Liga B", COLUMN_LEAGUE] = League.objects.get(symbol="LGT B")
    dfs.loc[dfs[COLUMN_LEAGUE] == "ACT", COLUMN_LEAGUE] = League.objects.get(name="EUSKO LABEL LIGA")
    dfs.loc[dfs[COLUMN_LEAGUE] == "-", COLUMN_LEAGUE] = None

    return dfs


def _load_races_and_check_errors(dfs: pd.DataFrame, is_female: bool) -> tuple[list[str], list[str]]:
    not_found = []
    unmatched = []
    play_off = Trophy.objects.get(name="PLAY-OFF LGT")
    play_off_act = Trophy.objects.get(name="PLAY-OFF ACT")
    gender = GENDER_FEMALE if is_female else GENDER_MALE

    for index, row in dfs.iterrows():
        if "race" in row and not pd.isna(row["race"]):  # pyright: ignore
            continue

        logger.debug(f"searching {row[COLUMN_NAME]} :: {row[COLUMN_DATE]}")
        try:
            if is_play_off(str(row[COLUMN_NAME])):
                dfs.at[index, "race"] = Race.objects.get(
                    Q(gender=gender) | Q(gender=GENDER_ALL),
                    date=row[COLUMN_DATE],
                    trophy=play_off if "LGT" in row[COLUMN_NAME] else play_off_act,
                )
                continue
            dfs.at[index, "race"] = Race.objects.get(date=row[COLUMN_DATE], league=row[COLUMN_LEAGUE])
        except Race.DoesNotExist:
            not_found.append(f"{row[COLUMN_DATE]}::{row[COLUMN_NAME]}")
        except Race.MultipleObjectsReturned:
            race_name = remove_genders(remove_parenthesis(str(row[COLUMN_NAME])))
            trophy = TrophyService.get_closest_by_name_or_none(race_name)
            flag = FlagService.get_closest_by_name_or_none(race_name)
            try:
                dfs.at[index, "race"] = RaceService.get_closest_match(
                    trophy,
                    flag,
                    league=row[COLUMN_LEAGUE],  # pyright: ignore
                    gender=gender,
                    date=row[COLUMN_DATE],  # pyright: ignore
                )
            except Race.DoesNotExist:
                not_found.append(f"{row[COLUMN_DATE]}::{row[COLUMN_NAME]}")
            except Race.MultipleObjectsReturned:
                unmatched.append(f"{row[COLUMN_DATE]}::{row[COLUMN_NAME]}")

    return not_found, unmatched


def _input_races(dfs: pd.DataFrame):
    for index, row in dfs.iterrows():
        if not pd.isna(row["race"]):  # pyright: ignore
            continue

        race_id = inquirer.text(f"no race found for {row[COLUMN_DATE]}::{row[COLUMN_NAME]}. Race ID", default=None)
        if race_id:
            race = Race.objects.get(id=race_id)
            dfs.at[index, "race"] = race


def _create_missing_races(dfs: pd.DataFrame, is_female: bool):
    for index, row in dfs.iterrows():
        if not pd.isna(row["race"]):  # pyright: ignore
            continue

        print(f"{row[COLUMN_DATE]} :: {row[COLUMN_NAME]}")
        (trophy, trophy_edition) = input_trophy(str(row[COLUMN_NAME]))
        (flag, flag_edition) = input_flag(str(row[COLUMN_NAME]))
        ttype = RACE_TIME_TRIAL if inquirer.confirm("Is this race a time trial?", default=False) else RACE_CONVENTIONAL

        new_race = Race(
            laps=int(row[COLUMN_NUMBER_LAPS]) if pd.isna(row[COLUMN_NUMBER_LAPS]) else None,  # pyright: ignore
            lanes=int(row[COLUMN_NUMBER_LANES]) if pd.isna(row[COLUMN_NUMBER_LANES]) else None,  # pyright: ignore
            type=ttype,
            date=row[COLUMN_DATE],
            day=1,
            race_name=row[COLUMN_NAME],
            trophy=trophy,
            trophy_edition=trophy_edition,
            flag=flag,
            flag_edition=flag_edition,
            league=row[COLUMN_LEAGUE],
            modality=RACE_TRAINERA,
            gender=GENDER_FEMALE if is_female else GENDER_MALE,
            metadata={"datasource": []},
        )

        logger.debug(json.dumps(RaceSerializer(new_race).data, indent=4, skipkeys=True, ensure_ascii=False))
        new_race.save()
        dfs.at[index, "race"] = new_race


def _update_existing_races(dfs: pd.DataFrame, entity: Entity, is_female: bool):
    for _, row in dfs.iterrows():
        if pd.isna(row["race"]):  # pyright: ignore
            continue

        race: Race = row["race"]  # pyright: ignore
        if row[COLUMN_EDITION] != race.flag_edition and row[COLUMN_EDITION] != race.trophy_edition:
            text = f"found flag edition {race.flag_edition}, provided one is {row[COLUMN_EDITION]}"
            if race.flag_edition and inquirer.confirm(f"{text}. Do you want to update it?", default=False):
                race.flag_edition = int(row[COLUMN_EDITION])
            text = f"found trophy edition {race.trophy_edition}, provided one is {row[COLUMN_EDITION]}"
            if race.trophy_edition and inquirer.confirm(f"{text}. Do you want to update it?", default=False):
                race.trophy_edition = int(row[COLUMN_EDITION])
            race.save()

        try:
            participant = Participant.objects.get(race=row["race"], club=entity)
            if row[COLUMN_DISTANCE]:  # pyright: ignore
                participant.distance = int(row[COLUMN_DISTANCE])
                participant.save()
        except Participant.DoesNotExist:
            participant = Participant(
                race=race,
                club=entity,
                distance=row[COLUMN_DISTANCE],
                laps=[row[COLUMN_TIME]] if pd.isna(row[COLUMN_TIME]) else [],  # pyright: ignore
                lane=row[COLUMN_LANE],
                gender=GENDER_FEMALE if is_female else GENDER_MALE,
                category=PARTICIPANT_CATEGORY_ABSOLUT,
            )
            participant.save()
