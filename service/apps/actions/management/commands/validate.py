import logging
import sys
from typing import Any, List

import pandas as pd
from django.core.management import BaseCommand
from pandas import DataFrame
from service.ai_django.ai_core.utils.shortcuts import all_or_none
from utils.choices import GENDERS

from apps.entities.models import Entity, League
from apps.entities.services import EntityService, LeagueService
from apps.races.models import Flag, Race, Trophy
from apps.races.services import FlagService, TrophyService

logger = logging.getLogger(__name__)

COLUMN_NAME = "name"
COLUMN_DATE = "t_date"
COLUMN_EDITION = "edition"
COLUMN_DAY = "day"
COLUMN_MODALITY = "modality"
COLUMN_LEAGUE = "league"
COLUMN_TOWN = "town"
COLUMN_ORGANIZER = "organizer"

COLUMN_GENDER = "gender"
COLUMN_CATEGORY = "category"
COLUMN_CNAME = "club_name"
COLUMN_LANE = "lane"
COLUMN_SERIES = "series"
COLUMN_LAPS = "laps"
COLUMN_DISTANCE = "distance"

COLUMN_TROPHY = "trophy_name"
COLUMN_CLUB = "participant"
COLUMN_RACE_ID = "race_id"
COLUMN_URL = "url"
COLUMN_DATASOURCE = "datasource"

COLUMN_RACE_LANES = "race_lanes"
COLUMN_RACE_LAPS = "race_laps"
COLUMN_CANCELLED = "cancelled"
COLUMN_DISQUALIFIED = "disqualified"

# computed columns
COMPUTED_TROPHY = "db_trophy"
COMPUTED_FLAG = "db_flag"
COMPUTED_RACE = "db_race"
COMPUTED_PARTICIPANT = "db_club"


class Command(BaseCommand):
    help = "Validate CSV file to be imported"

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="+", type=str)

    def handle(self, *args, **options):
        for file in options["path"]:
            validate_file(file)


####################################################
#                VALIDATION METHODS                #
####################################################
def validate_file(file: str, manual: bool = False):
    dfs = pd.read_csv(filepath_or_buffer=file, sep=",", header=0, dtype=str, parse_dates=[COLUMN_DATE]).fillna("")

    errors = {
        # check column types
        "invalid_series": _check_type(dfs, COLUMN_SERIES, int),
        "invalid_lane": _check_type(dfs, COLUMN_LANE, int),
        "invalid_edition": _check_type(dfs, COLUMN_EDITION, int),
        "invalid_day": _check_type(dfs, COLUMN_DAY, int),
        "invalid_race_lanes": _check_type(dfs, COLUMN_RACE_LANES, int) if COLUMN_RACE_LANES in dfs else [],
        "invalid_race_laps": _check_type(dfs, COLUMN_RACE_LAPS, int) if COLUMN_RACE_LAPS in dfs else [],
        "invalid_gender": _check_valid_gender(dfs),
        "invalid_town": _check_valid_town(dfs),
        # check race miss matches
        "race_lanes_values": _check_single_value(dfs, COLUMN_RACE_LANES),
        "race_laps_values": _check_single_value(dfs, COLUMN_RACE_LAPS),
        "organizer_values": _check_single_value(dfs, COLUMN_ORGANIZER),
        "town_values": _check_single_value(dfs, COLUMN_TOWN),
        # check null values
        "null_trophy": _check_null_values(dfs, COLUMN_TROPHY),
        "null_club": _check_null_values(dfs, COLUMN_CLUB),
        "null_date": _check_null_values(dfs, COLUMN_DATE),
        "null_race_id": _check_null_values(dfs, COLUMN_RACE_ID) if COLUMN_RACE_ID in dfs else [],
        # check non-existing values
        "league_not_found": _check_leagues(dfs[COLUMN_LEAGUE].unique()),
        "league_gender_error": _check_gender(dfs),
        "club_not_found": _check_clubs(dfs[COLUMN_CLUB].unique()),
        "organizer_not_found": _check_clubs(dfs[COLUMN_ORGANIZER].unique()),
        "trophies_not_found": _check_trophies(dfs[COLUMN_TROPHY].unique()),
    }

    ignored_errors = ["trophies_not_found"] if manual else []
    if any(len(errors[k]) and k not in ignored_errors for k in errors.keys()):  # check we don't have breaking errors
        [logger.error(f"{k}: {errors[k]}") for k in errors.keys() if k not in ignored_errors]
        sys.exit(1)


def _check_type(dfs: DataFrame, column: str, ttype) -> List[Any]:
    invalid = []
    for index, item in enumerate(dfs[column]):
        try:
            ttype(item)
        except ValueError:
            invalid.append(f"Invalid type {type(item)} found in column {column} in row {index + 2}. {ttype} required")
    return invalid


def _check_single_value(dfs: DataFrame, column: str) -> List[Any]:
    invalid = []
    race_ids = dfs[COLUMN_RACE_ID].unique() if COLUMN_RACE_ID in dfs else []
    for race_id in race_ids:
        if len(dfs.loc[dfs[COLUMN_RACE_ID] == race_id][column].unique()) > 1:
            invalid.append(f"Invalid values found in column {column} for race {race_id}")
    return invalid


def _check_valid_gender(dfs: DataFrame) -> List[Any]:
    invalid = []
    for itx, item in enumerate(dfs[COLUMN_GENDER]):
        if item and item not in GENDERS:
            invalid.append(f"Invalid gender for race {itx + 1}")
    return invalid


def _check_valid_town(dfs: DataFrame) -> List[Any]:
    invalid = []
    towns = Race.objects.distinct("town").order_by("town").values_list("town", flat=True)
    for itx, item in enumerate(dfs[COLUMN_TOWN]):
        if item and item not in towns:
            invalid.append(f"Invalid town for race {itx + 1}")
    return invalid


def _check_null_values(dfs: DataFrame, column: str) -> List[Any]:
    null = []
    for index, item in enumerate(dfs[column]):
        if not item:
            null.append(f"Null {column} found in row {index + 2}")
    return null


def _check_leagues(names: List[str]) -> List[str]:
    not_found = []
    for name in [n for n in names if n]:
        try:
            LeagueService.get_by_name(name)
        except League.DoesNotExist:
            not_found.append(name)
    return not_found


def _check_gender(dfs: DataFrame) -> List[str]:
    errors = []
    for _, row in dfs.iterrows():
        if all_or_none([row[COLUMN_LEAGUE], row[COLUMN_GENDER]]):
            errors.append(f"league: {row[COLUMN_LEAGUE]} || gender: {row[COLUMN_GENDER]}")
    return errors


def _check_clubs(names: List[str]) -> List[str]:
    not_found = []
    for name in [n for n in names if n]:
        try:
            EntityService.get_closest_by_name_type(name)
        except Entity.DoesNotExist:
            not_found.append(name)
    return not_found


def _check_trophies(names: List[str]) -> List[str]:
    not_found = []
    for name in [n for n in names if n]:
        try:
            TrophyService.get_closest_by_name(name)
        except Trophy.DoesNotExist:
            FlagService.get_closest_by_name(name)
        except Flag.DoesNotExist:
            not_found.append(name)
    return not_found
