import datetime
import itertools
import logging
import os
import sys
from ast import literal_eval
from datetime import time
from typing import Optional, Dict, List, Tuple, Any

import inquirer
import pandas as pd
from django.core.management import BaseCommand
from pandas import DataFrame, Series

from apps.entities.models import League, Entity, LEAGUE_GENDERS
from apps.entities.services import LeagueService, EntityService
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from apps.races.models import Trophy, Race, RACE_TIME_TRIAL, RACE_CONVENTIONAL, Flag
from apps.races.services import TrophyService, RaceService, FlagService
from digest.scrappers import ACTScrapper, LGTScrapper
from utils.checks import is_play_off
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)

COLUMN_LEAGUE = 'league'
COLUMN_GENDER = 'gender'
COLUMN_NAME = 'name'
COLUMN_TROPHY = 'trophy_name'
COLUMN_EDITION = 'edition'
COLUMN_DAY = 'day'
COLUMN_DATE = 't_date'
COLUMN_TOWN = 'town'
COLUMN_ORGANIZER = 'organizer'
COLUMN_CANCELLED = 'cancelled'
COLUMN_CNAME = 'club_name'
COLUMN_CLUB = 'participant'
COLUMN_LANE = 'lane'
COLUMN_DISQUALIFIED = 'disqualified'
COLUMN_RACE_LANES = 'race_lanes'
COLUMN_SERIES = 'series'
COLUMN_LAPS = 'laps'
COLUMN_RACE_LAPS = 'race_laps'
COLUMN_DISTANCE = 'distance'
COLUMN_RACE_ID = 'race_id'
COLUMN_URL = 'url'
COLUMN_DATASOURCE = 'datasource'

# computed columns
COMPUTED_TROPHY = 'db_trophy'
COMPUTED_FLAG = 'db_flag'
COMPUTED_RACE = 'db_race'
COMPUTED_GENDER = 'db_gender'

_KNOWN_MAPPINGS = {
    'BANDEIRA XUNTA DE GALICIA': ['CAMPEONATO GALEGO DE TRAINERAS'],
}


# noinspection Assert
class Command(BaseCommand):
    """
    Options:
        --manual: Allows non existing trophies/flags that will be created with user input.
        --validate: Do a simple validation of the file.
    Valid CSV columns:
        name: str                   || Will be saved in the database as is (#Race.race_name).
        trophy_name: Optional[str]  || Will be used for search the #Trophy or #Flag and for normalization (defaults to name).
        club_name: str              || Will be saved in the database as is (#Participant.club_name).
        participant: Optional[str]  || Will be used for search #Entity[type=CLUB] and normalization (defaults to club_name).
        t_date: date                || Used to find or create a #Race - (YYYY-MM-DD).

        league: Optional[str]       || The name of the league #League.name.
        gender: Optional[str]       || (#Race.gender) 'FEMALE' | 'MALE'.
        edition: int                || The edition of the race if known, will be used for #Trophy, #Flag or both.
        day: int                    || #Race.day for races that happen in multiple days.
        town: Optional[str]         || The town where the race was celebrated.
        organizer: Optional[str]    || The #Entity organizing the event.
        race_laps: Optional[int]    || Precomputed number of laps for the #Race.laps
        race_lanes: Optional[int]   || Precomputed number of lanes for the #Race.lanes
        cancelled: Optional[bool]   || If the race was cancelled for some reason

        series: int                 || #Participant.series
        lane: int                   || #Participant.lane
        laps: List[str]             || #Participant.laps (HH:mm:ss.xxx)
        disqualified: Optional[bool]|| If the participant was disqualified for some reason

        race_id: str                || The ID of the race in the datasource
        url: Optional[str]          || Datasource URL where the race was found
        datasource: str             || Datasource where the race was found
    NOTES:
        - One of 'league', 'gender' is required.
        - Only one of 'league', 'gender' is accepted.
    DEFAULTS:
        - cancelled = False
        - disqualified = False
    """

    help = 'Import CSV file into the DB'

    __CACHE: Dict[str, List[Tuple[str, Any]]] = {
        'leagues': [],
        'clubs': [],
        'trophies': [],
        'flags': [],
    }

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)
        parser.add_argument('--manual', action='store_true', default=False)
        parser.add_argument('--only-validate', action='store_true', default=False)

    def handle(self, *args, **options):
        assert options['path']

        for file in options['path']:
            assert os.path.isfile(file)

            self._validate(file, manual=options['manual'])
            if options['only_validate']:
                return

            dfs = self._prepare_dataframe(
                pd.read_csv(
                    filepath_or_buffer=file,
                    sep=',',
                    header=0,
                    skip_blank_lines=True,
                    converters={
                        COLUMN_LAPS: lambda v: [time.fromisoformat(i) for i in literal_eval(v) if i != '00:00:00'],
                        COLUMN_DATE: lambda v: datetime.date.fromisoformat(v)
                    }
                ).fillna('')
            )

            # create missing trophies/flags
            missing_trophies = dfs.loc[dfs[COMPUTED_TROPHY].isnull() & dfs[COMPUTED_FLAG].isnull()][COLUMN_TROPHY].unique()
            if len(missing_trophies) > 0:
                if not options['manual']:
                    raise StopProcessing(f'missing: {missing_trophies}')
                self._create_trophy_or_flag(dfs, missing_trophies)

            # check all missing trophies/flags where created
            if len(dfs.loc[dfs[COMPUTED_TROPHY].isnull() & dfs[COMPUTED_FLAG].isnull()][COLUMN_TROPHY].unique()) > 0:
                raise StopProcessing

            for race_id, gender in list(itertools.product(dfs[COLUMN_RACE_ID].unique(), dfs[COMPUTED_GENDER].unique())):
                if dfs.loc[(dfs[COLUMN_RACE_ID] == race_id) & (dfs[COMPUTED_GENDER] == gender)].empty:
                    continue
                logger.debug(f'processing race {race_id}')
                self._get_race_or_create(dfs, dfs.loc[(dfs[COLUMN_RACE_ID] == race_id) & (dfs[COMPUTED_GENDER] == gender)].iloc[0])

            for index, row in dfs.iterrows():
                logger.debug(f'processing row {index}')
                self._create_or_update_participant(row)

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def _prepare_dataframe(self, dfs: DataFrame) -> DataFrame:
        # fill optional columns
        dfs[COLUMN_TROPHY] = dfs[COLUMN_TROPHY] if COLUMN_TROPHY in dfs else dfs[COLUMN_NAME]
        dfs[COLUMN_CLUB] = dfs[COLUMN_CLUB] if COLUMN_CLUB in dfs else dfs[COLUMN_CNAME]

        # computed columns
        dfs[COLUMN_RACE_ID] = dfs.apply(lambda x: x[COLUMN_RACE_ID] if COLUMN_RACE_ID in x else self._get_datasource_id(x), axis=1)
        dfs[COLUMN_LEAGUE] = dfs.apply(lambda x: x[COLUMN_LEAGUE] if is_play_off(x[COLUMN_TROPHY]) else None, axis=1)

        # find already existing data
        dfs[COMPUTED_TROPHY] = dfs.apply(lambda x: self._get_trophy(x[COLUMN_TROPHY]), axis=1)
        dfs[COMPUTED_FLAG] = dfs.apply(lambda x: self._get_flag(x[COLUMN_TROPHY]), axis=1)
        dfs[COMPUTED_RACE] = dfs.apply(lambda x: None, axis=1)
        dfs[COLUMN_LEAGUE] = dfs.apply(lambda x: self._get_league(x[COLUMN_LEAGUE]), axis=1)
        dfs[COLUMN_CLUB] = dfs.apply(lambda x: self._get_club(x[COLUMN_CLUB]), axis=1)
        dfs[COLUMN_ORGANIZER] = dfs.apply(lambda x: self._get_organizer(x[COLUMN_ORGANIZER]), axis=1)
        dfs[COMPUTED_GENDER] = dfs.apply(lambda x: x[COLUMN_LEAGUE].gender if x[COLUMN_LEAGUE] else x[COLUMN_GENDER], axis=1)

        date_pairs = self._date_pairs(dfs.loc[dfs[COLUMN_DAY] == 1][COLUMN_DATE].unique())
        for start, end in date_pairs:
            self._fix_days(dfs, start, end, column=COMPUTED_TROPHY)
            self._fix_days(dfs, start, end, column=COMPUTED_FLAG)

        return dfs

    @staticmethod
    def _get_datasource_id(dfs: DataFrame) -> str:
        match dfs[COLUMN_DATASOURCE]:
            case ACTScrapper.DATASOURCE:
                return dfs[COLUMN_URL].split('r=')[-1]
            case LGTScrapper.DATASOURCE:
                return dfs[COLUMN_URL].split('/')[-1]
        return ''

    @staticmethod
    def _fix_days(dfs: DataFrame, start: datetime.date, end: datetime.date, column: str):
        for _, row in dfs.loc[(dfs[COLUMN_DATE] == start) & (dfs[COLUMN_DAY] == 1)].iterrows():
            matches = dfs.loc[(dfs[COLUMN_DATE] == end) & (dfs[column] == row[column]) & (dfs[COLUMN_DAY] == 1) &
                              ((row[COLUMN_LEAGUE] is None) | (dfs[COLUMN_LEAGUE] == row[COLUMN_LEAGUE])) &
                              ((row[COLUMN_GENDER] is None) | (dfs[COLUMN_GENDER] == row[COLUMN_GENDER]))]

            if not matches.empty:
                logger.info(f'updating day for {end}:: {matches.index}')
                dfs.loc[matches.index, [COLUMN_DAY]] = 2

    @staticmethod
    def _get_race_laps(dfs: DataFrame, row: Series) -> int:
        laps = row[COLUMN_RACE_LAPS]
        if not laps:
            laps = max([len(e) for e in dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LAPS]])
        if laps > 6:
            logger.warning(f'race found with more than 6 laps: {row[COLUMN_RACE_ID]}')
        return laps

    @staticmethod
    def _get_race_lanes(dfs: DataFrame, row: Series) -> int:
        lanes = row[COLUMN_RACE_LANES]
        if not lanes:
            lanes = dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LANE].max()
        if lanes > 5:
            logger.warning(f'race found with more than 5 lanes: {row[COLUMN_RACE_ID]}')
        return lanes

    @staticmethod
    def _get_race_type(dfs: DataFrame, row: Series) -> str:
        lanes = row[COLUMN_RACE_LANES]
        if not lanes:
            lanes = dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LANE].max()
        return RACE_TIME_TRIAL if lanes == 1 else RACE_CONVENTIONAL

    @staticmethod
    def _get_distance(row: Series, race: Race) -> int:
        if COLUMN_DISTANCE in row:
            return row[COLUMN_DISTANCE]

        short_leagues = ['LIGA EUSKOTREN', 'EMAKUMEZKO TRAINERUEN ELKARTEA', 'ASOCIACIÓN DE CLUBES DE TRAINERAS']
        is_short = race.is_female and race.league and race.league.name in short_leagues
        if is_short:
            logger.warning(f'distance might be incorrect for {race} races')
        return 2778 if is_short else 5556

    ####################################################
    #                DB ACCESS METHODS                 #
    ####################################################

    def _get_league(self, league: str) -> Optional[League]:
        if not league:
            return None

        # try to find in the memory cache
        for key, value in self.__CACHE['leagues']:
            if key == league:
                return value

        found_league = LeagueService.get_by_name(league)
        self.__CACHE['leagues'].append((league, found_league))
        return found_league

    def _get_club(self, club: str) -> Entity:
        assert club

        # try to find in the memory cache
        for key, value in self.__CACHE['clubs']:
            if key == club:
                return value

        # search in database
        found_club = EntityService.get_closest_club_by_name(club)
        self.__CACHE['clubs'].append((club, found_club))
        return found_club

    def _get_organizer(self, club: Optional[str]) -> Optional[Entity]:
        if not club:
            return None

        # try to find in the memory cache
        for key, value in self.__CACHE['clubs']:
            if key == club:
                return value

        # search in database
        found_organizer = EntityService.get_closest_by_name_type(club)
        self.__CACHE['clubs'].append((club, found_organizer))
        return found_organizer

    # noinspection DuplicatedCode
    def _get_trophy(self, trophy: str) -> Optional[Trophy]:
        for k, v in _KNOWN_MAPPINGS.items():
            if trophy in v or any(part in trophy for part in v):
                trophy = k
                break

        # try to find in the memory cache
        for key, value in self.__CACHE['trophies']:
            if key == trophy:
                return value

        # search in database
        try:
            found_trophy = TrophyService.get_closest_by_name(trophy)
            self.__CACHE['trophies'].append((trophy, found_trophy))
            return found_trophy
        except Trophy.DoesNotExist:
            return None

    def _get_flag(self, flag: str) -> Optional[Flag]:
        for k, v in _KNOWN_MAPPINGS.items():
            if flag in v or any(part in flag for part in v):
                flag = k
                break

        # try to find in the memory cache
        for key, value in self.__CACHE['flags']:
            if key == flag:
                return value

        # search in database
        try:
            found_flag = FlagService.get_closest_by_name(flag)
            self.__CACHE['flags'].append((flag, found_flag))
            return found_flag
        except Flag.DoesNotExist:
            return None

    ####################################################
    #                 CREATION METHODS                 #
    ####################################################

    @staticmethod
    def _create_trophy_or_flag(dfs: DataFrame, trophies: List[str]):
        if not inquirer.confirm(f"This needs to create new Trophies or Flags for:\n {trophies}\n Continue?", default=False):
            raise StopProcessing

        for t_name in trophies:
            name = t_name[2:] if t_name[1].isspace() else t_name
            menu = inquirer.list_input(message=f'What to do with {name}?', choices=['Create Trophy', 'Create Flag', 'Cancel'])
            match menu.lower():
                case 'create trophy':
                    new_name = inquirer.text(f'Rename trophy {name} to:')
                    if new_name:
                        trophy = TrophyService.get_closest_by_name_or_create(name=new_name)
                    else:
                        trophy = Trophy(name=name.upper())
                        trophy.save()
                        logger.info(f'created:: {trophy}')

                    dfs[COMPUTED_TROPHY].mask(dfs[COLUMN_TROPHY] == t_name, trophy, inplace=True)
                case 'create flag':
                    new_name = inquirer.text(f'Rename flag {name} to:')
                    if new_name:
                        flag = FlagService.get_closest_by_name_or_create(name=new_name)
                    else:
                        flag = Flag(name=name.upper())
                        flag.save()
                        logger.info(f'created:: {flag}')

                    dfs[COMPUTED_FLAG].mask(dfs[COLUMN_TROPHY] == t_name, flag, inplace=True)
                case _:
                    raise StopProcessing

    def _get_race_or_create(self, dfs: DataFrame, row: Series):
        race = Race(
            date=row[COLUMN_DATE],
            league=row[COLUMN_LEAGUE],
            gender=row[COLUMN_GENDER],
            trophy=row[COMPUTED_TROPHY],
            trophy_edition=row[COLUMN_EDITION] if row[COMPUTED_TROPHY] else None,
            flag=row[COMPUTED_FLAG],
            flag_edition=row[COLUMN_EDITION] if row[COMPUTED_FLAG] else None,
            day=row[COLUMN_DAY],
            race_name=row[COLUMN_NAME],  # un-normalized race name
            town=row[COLUMN_TOWN],
            organizer=row[COLUMN_ORGANIZER],
            lanes=self._get_race_lanes(dfs, row),
            laps=self._get_race_laps(dfs, row),
            type=self._get_race_type(dfs, row),
            cancelled=row[COLUMN_CANCELLED] if COLUMN_CANCELLED in row else False,
            metadata={
                "datasource": [
                    {
                        'race_id': row[COLUMN_RACE_ID],
                        'datasource_name': row[COLUMN_DATASOURCE],
                        "values": [{
                            "details_page": row[COLUMN_URL]
                        }] if COLUMN_URL in row and row[COLUMN_URL] else []
                    }
                ]
            },
        )
        created, db_race = RaceService.get_race_or_create(race)
        if not created:
            self._compare(race, db_race)

            if not any(x['datasource_name'] == row[COLUMN_DATASOURCE] for x in db_race.metadata["datasource"]):
                db_race.metadata['datasource'].append(race.metadata['datasource'].pop())
                db_race.save()
        # TODO: fix 'editions', we should probably do it here

        condition = (dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]) & (dfs[COMPUTED_GENDER] == row[COMPUTED_GENDER])
        dfs[COMPUTED_RACE].mask(condition, db_race, inplace=True)

    def _create_or_update_participant(self, row: Series):
        participant = Participant(
            club=row[COLUMN_CLUB],
            club_name=row[COLUMN_CNAME],  # un-normalized used club name
            race=row[COMPUTED_RACE],
            distance=self._get_distance(row, row[COMPUTED_RACE]),
            lane=row[COLUMN_LANE],
            laps=row[COLUMN_LAPS],
            series=row[COLUMN_SERIES],
            disqualified=row[COLUMN_DISQUALIFIED] if COLUMN_DISQUALIFIED in row else False,
        )
        created, db_participant = ParticipantService.get_participant_or_create(participant)
        if not created:
            self._compare(participant, db_participant)

    ####################################################
    #           PRIVATE VALIDATION METHODS             #
    ####################################################
    def _validate(self, file: str, manual: bool = False):
        dfs = pd.read_csv(filepath_or_buffer=file, sep=',', header=0, dtype=str, parse_dates=[COLUMN_DATE]).fillna('')

        errors = {
            # check column types
            'invalid_series': self._check_type(dfs, COLUMN_SERIES, int),
            'invalid_lane': self._check_type(dfs, COLUMN_LANE, int),
            'invalid_edition': self._check_type(dfs, COLUMN_EDITION, int),
            'invalid_day': self._check_type(dfs, COLUMN_DAY, int),
            'invalid_race_lanes': self._check_type(dfs, COLUMN_RACE_LANES, int) if COLUMN_RACE_LANES in dfs else [],
            'invalid_race_laps': self._check_type(dfs, COLUMN_RACE_LAPS, int) if COLUMN_RACE_LAPS in dfs else [],
            'invalid_gender': self._check_valid_gender(dfs),
            'invalid_town': self._check_valid_town(dfs),
            # check race miss matches
            'race_lanes_values': self._check_single_value(dfs, COLUMN_RACE_LANES),
            'race_laps_values': self._check_single_value(dfs, COLUMN_RACE_LAPS),
            'organizer_values': self._check_single_value(dfs, COLUMN_ORGANIZER),
            'town_values': self._check_single_value(dfs, COLUMN_TOWN),
            # check null values
            'null_trophy': self._check_null_values(dfs, COLUMN_NAME),
            'null_club': self._check_null_values(dfs, COLUMN_CLUB),
            'null_date': self._check_null_values(dfs, COLUMN_DATE),
            'null_race_id': self._check_null_values(dfs, COLUMN_RACE_ID) if COLUMN_RACE_ID in dfs else [],
            # check non-existing values
            'league_not_found': self._check_leagues(dfs[COLUMN_LEAGUE].unique()),
            'league_gender_error': self._check_gender(dfs),
            'club_not_found': self._check_clubs(dfs[COLUMN_CLUB].unique()),
            'organizer_not_found': self._check_clubs(dfs[COLUMN_ORGANIZER].unique()),
            'trophies_not_found': self._check_trophies(dfs[COLUMN_NAME].unique()),
        }

        self._check_trophies(dfs[COLUMN_TROPHY].unique())

        ignored_errors = ['trophies_not_found'] if manual else []
        if any(len(errors[k]) and k not in ignored_errors for k in errors.keys()):  # check we don't have breaking errors
            [logger.error(f'{k}: {errors[k]}') for k in errors.keys() if k not in ignored_errors]
            sys.exit(1)

    @staticmethod
    def _check_type(dfs: DataFrame, column: str, ttype) -> List[Any]:
        invalid = []
        for index, item in enumerate(dfs[column]):
            try:
                ttype(item)
            except ValueError:
                invalid.append(f'Invalid type {type(item)} found in column {column} in row {index + 2}. {ttype} required')
        return invalid

    @staticmethod
    def _check_single_value(dfs: DataFrame, column: str) -> List[Any]:
        invalid = []
        race_ids = dfs[COLUMN_RACE_ID].unique() if COLUMN_RACE_ID in dfs else []
        for race_id in race_ids:
            if len(dfs.loc[dfs[COLUMN_RACE_ID] == race_id][column].unique()) > 1:
                invalid.append(f'Invalid values found in column {column} for race {race_id}')
        return invalid

    @staticmethod
    def _check_valid_gender(dfs: DataFrame) -> List[Any]:
        invalid = []
        for itx, item in enumerate(dfs[COLUMN_GENDER]):
            if item and item not in LEAGUE_GENDERS:
                invalid.append(f'Invalid gender for race {itx + 1}')
        return invalid

    @staticmethod
    def _check_valid_town(dfs: DataFrame) -> List[Any]:
        invalid = []
        towns = Race.objects.distinct('town').order_by('town').values_list('town', flat=True)
        for itx, item in enumerate(dfs[COLUMN_TOWN]):
            if item and item not in towns:
                invalid.append(f'Invalid town for race {itx + 1}')
        return invalid

    @staticmethod
    def _check_null_values(dfs: DataFrame, column: str) -> List[Any]:
        null = []
        for index, item in enumerate(dfs[column]):
            if not item:
                null.append(f'Null {column} found in row {index + 2}')
        return null

    @staticmethod
    def _check_leagues(names: List[str]) -> List[str]:
        not_found = []
        for name in [n for n in names if n]:
            try:
                LeagueService.get_by_name(name)
            except League.DoesNotExist:
                not_found.append(name)
        return not_found

    @staticmethod
    def _check_gender(dfs: DataFrame) -> List[str]:
        errors = []
        for _, row in dfs.iterrows():
            if all(x for x in [row[COLUMN_LEAGUE], row[COLUMN_GENDER]]) or all(not x for x in [row[COLUMN_LEAGUE], row[COLUMN_GENDER]]):
                errors.append(f'league: {row[COLUMN_LEAGUE]} || gender: {row[COLUMN_GENDER]}')
        return errors

    @staticmethod
    def _check_clubs(names: List[str]) -> List[str]:
        not_found = []
        for name in [n for n in names if n]:
            try:
                EntityService.get_closest_by_name_type(name)
            except Entity.DoesNotExist:
                not_found.append(name)
        return not_found

    @staticmethod
    def _check_trophies(names: List[str]) -> List[str]:
        not_found = []
        for name in [n for n in names if n]:
            try:
                TrophyService.get_closest_by_name(name)
            except Trophy.DoesNotExist:
                not_found.append(name)
        return not_found

    @staticmethod
    def _compare(e1: Race | Participant, e2: Race | Participant):
        ignored_keys = ['id', 'metadata', 'creation_date', 'distance', 'club_name', 'race_name']
        keys = [k for k in e1.__dict__.keys() if not k.startswith('_') and k not in ignored_keys]
        for k in keys:
            if e1.__dict__[k] != e2.__dict__[k]:
                logger.warning(f'mismatch({k}) between: {e1}({e1.__dict__[k]}) and {e2}({e2.__dict__[k]})')

    @staticmethod
    def _date_pairs(dates: List[datetime.date]) -> List[Tuple[datetime.date, datetime.date]]:
        dates = sorted(dates)

        pairs = []
        start = dates[0]
        for i in range(1, len(dates)):
            if dates[i] == start + datetime.timedelta(days=1):
                pairs.append((start, dates[i]))
            start = dates[i]

        return pairs
