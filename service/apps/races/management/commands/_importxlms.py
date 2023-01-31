import logging
import os
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any

import pandas as pd
from django.core.management.base import BaseCommand
from pandas import DataFrame, Series

from ai_django.ai_core.utils.strings import roman_to_int, remove_conjunctions
from apps.entities.models import Entity, League
from apps.entities.services import EntityService, LeagueService
from apps.participants.models import Participant
from apps.races.models import RACE_CONVENTIONAL, RACE_TIME_TRIAL, Trophy, Race
from apps.races.normalization import normalize_trophy_name
from apps.races.schemas import default_race_metadata
from apps.races.services import TrophyService, RaceService
from utils.checks import is_play_off
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)

COLUMN_NAME = 'Nome'
COLUMN_DATE = 'Fecha'
COLUMN_CLUB = 'Club'
COLUMN_LEAGUE = 'Liga'
COLUMN_ORGANIZER = 'Organizador'
COLUMN_EDITION = 'Edición'
COLUMN_DAY = 'DAY'
COLUMN_TIME = 'Tiempo'
COLUMN_LANE = 'Boya'
COLUMN_DISTANCE = 'Distancia'
COLUMN_RACE_LANES = 'N Boyas'
COLUMN_RACE_LAPS = 'N Largos'
COLUMN_RACE_TYPE = 'Tipo'

# computed columns
COMPUTED_TROPHY = 'db_trophy'
COMPUTED_TOWN = 'db_town'


# noinspection DuplicatedCode
class Command(BaseCommand):
    help = 'Import my custom XLMS file into the db.'

    __CACHE: Dict[str, List[Tuple[str, Any]]] = {
        'leagues': [],
        'trophies': [],
    }
    __TYPE_MAP = {
        'Convencional': RACE_CONVENTIONAL,
        'Contrarreloxo': RACE_TIME_TRIAL,
    }

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)

    def handle(self, *args, **options):
        for file in options['path']:
            assert os.path.isfile(file)

            dfs = self.__prepare_dataframe(
                pd.concat(pd.read_excel(file, sheet_name=None, header=0, parse_dates=[COLUMN_DATE]), ignore_index=True).fillna('')
            )

            # create missing trophies
            missing_trophies = dfs.loc[dfs[COMPUTED_TROPHY].isnull()][COLUMN_NAME].unique()
            if len(missing_trophies) > 0:
                self.__create_trophies(dfs, missing_trophies)

            print(dfs)
            for index, row in dfs.iterrows():
                logger.debug(f'processing row {index}')

                race = self.__get_race_or_create(row)
                self.__create_or_update_participant(row, race)

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def __prepare_dataframe(self, dfs: DataFrame) -> DataFrame:
        dfs.drop(dfs[dfs[COLUMN_NAME].isin(['', '-'])].index, inplace=True)

        dfs[COLUMN_CLUB] = dfs[COLUMN_CLUB].apply(lambda x: self.__get_club(x))
        dfs[COLUMN_LEAGUE] = dfs.apply(lambda x: self.__get_league(x[COLUMN_NAME], x[COLUMN_LEAGUE]), axis=1)
        dfs[COLUMN_ORGANIZER] = dfs[COLUMN_ORGANIZER].apply(lambda x: self.__get_organizer(x))
        dfs[COLUMN_EDITION] = dfs[COLUMN_EDITION].apply(lambda x: roman_to_int(x) if x and '-' not in x else 1)
        dfs[COLUMN_TIME] = dfs[COLUMN_TIME].apply(lambda x: self.__get_laps(x))
        dfs[COLUMN_DISTANCE] = dfs[COLUMN_DISTANCE].apply(lambda x: int(x) if x else None)
        dfs[COLUMN_DAY] = dfs[COLUMN_NAME].apply(lambda x: self.__get_day(x))
        dfs[COLUMN_RACE_TYPE] = dfs[COLUMN_RACE_TYPE].apply(lambda x: self.__TYPE_MAP[x] if x else RACE_CONVENTIONAL)

        dfs[COMPUTED_TOWN] = dfs.apply(lambda x: self.__normalize_race_name(x[COLUMN_NAME], x[COLUMN_LEAGUE])[1], axis=1)
        dfs[COLUMN_NAME] = dfs.apply(lambda x: self.__normalize_race_name(x[COLUMN_NAME], x[COLUMN_LEAGUE])[0], axis=1)

        self.__deduplicate_trophies(dfs)

        dfs[COMPUTED_TROPHY] = dfs.apply(lambda x: self.__get_trophy(x[COLUMN_NAME]), axis=1)

        return dfs

    @staticmethod
    def __get_laps(t: Optional[str]) -> List[str]:
        return [datetime.strptime(t, '%M:%S.%f').time().isoformat()] if t else []

    @staticmethod
    def __get_day(name: str) -> int:
        if 'XORNADA' in name:
            return int(re.findall(r' \d+', name)[0].strip())
        return 1

    @staticmethod
    def __normalize_race_name(name: str, league: Optional[League]) -> Tuple[str, Optional[str]]:
        is_female = league.is_female if league else False
        name = name.upper()
        town = None

        # find town in between ()
        match = re.findall(r'\((.*?)\)', name)
        if match:
            town = match[0].strip()
            if town in ['CLASIFICATORIA']:
                town = None
            else:
                name = name.replace(f'({town})', '')

        # find day in the name
        if 'XORNADA' in name:
            name = re.sub(r'(XORNADA )?\d+( XORNADA)?', '', name)

        return normalize_trophy_name(name, is_female=is_female), town

    @staticmethod
    def __deduplicate_trophies(dfs: DataFrame):
        for trophy in dfs[COLUMN_NAME].unique():
            c_trophy = remove_conjunctions(trophy)
            for t in dfs[COLUMN_NAME]:
                if c_trophy == remove_conjunctions(t):
                    dfs[COLUMN_NAME].mask(dfs[COLUMN_NAME] == t, trophy, inplace=True)

    @staticmethod
    def __value_or_default(value: Any, default: Any) -> Any:
        return value if value and value == value else default

    ####################################################
    #                 RETRIEVE METHODS                 #
    ####################################################
    @staticmethod
    def __get_club(name: str) -> Optional[Entity]:
        if not name:
            name = 'CLUB REMO PUEBLA'
        if name.upper() == 'PUEBLA-CABO':
            name = 'CLUB REMO CABO DE CRUZ'

        return EntityService.get_closest_club_by_name(name.upper())

    @staticmethod
    def __get_organizer(name: str) -> Optional[Entity]:
        if not name:
            return None
        name = name.upper()
        if name == 'ACT':
            name = 'ASOCIACIÓN DE CLUBES DE TRAINERAS'
        if name == 'LGT':
            name = 'LIGA GALEGA DE TRAIÑAS'

        return EntityService.get_closest_by_name_type(name)

    def __get_league(self, name: str, league: Optional[str]) -> Optional[League]:
        if is_play_off(name):
            if 'ACT' in name:
                league = 'ACT'
            else:
                league = 'LGT'

        if not league or league == '-':
            return None

        # try to find in the memory cache
        for key, value in self.__CACHE['leagues']:
            if key == league:
                return value

        found_league = LeagueService.get_by_name(league.upper())
        self.__CACHE['leagues'].append((league, found_league))
        return found_league

    def __get_trophy(self, trophy: str) -> Optional[Trophy]:
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

    ####################################################
    #                 CREATION METHODS                 #
    ####################################################

    def __get_race_or_create(self, row: Series) -> Race:
        try:
            raise NotImplementedError
            # race = RaceService.get_by_trophy_date_league(
            #     trophy=row[COMPUTED_TROPHY],
            #     date=row[COLUMN_DATE],
            #     league=row[COLUMN_LEAGUE],
            # )
        except Race.DoesNotExist:
            race = Race(
                league=row[COLUMN_LEAGUE],
                trophy=row[COMPUTED_TROPHY],
                organizer=row[COLUMN_ORGANIZER],
                edition=row[COLUMN_EDITION],
                town=row[COMPUTED_TOWN],
                date=row[COLUMN_DATE],
                day=row[COLUMN_DAY],
                lanes=self.__value_or_default(row[COLUMN_RACE_LANES], None),
                laps=self.__value_or_default(row[COLUMN_RACE_LAPS], None),
                type=row[COLUMN_RACE_TYPE],
                metadata=default_race_metadata(),
            )

            logger.info(f'creating race {race}')
            race.save()

        return race

    def __create_or_update_participant(self, row: Series, race: Race):
        try:
            participant = Participant.objects.get(club=row[COLUMN_CLUB], race=race)
            participant.distance = self.__value_or_default(row[COLUMN_DISTANCE], 5556)
            participant.lane = participant.lane if participant.lane else self.__value_or_default(row[COLUMN_LANE], None)

            logger.info(f'updating participant {participant}')
            participant.save()
        except Participant.DoesNotExist:
            participant = Participant(
                club=row[COLUMN_CLUB],
                race=race,
                distance=self.__value_or_default(row[COLUMN_DISTANCE], 5556),
                lane=self.__value_or_default(row[COLUMN_LANE], None),
                laps=row[COLUMN_TIME],
            )

            logger.info(f'creating participant {participant}')
            participant.save()

    def __create_trophies(self, dfs: DataFrame, trophies: List[str]):
        logger.info(f'creating new trophies {trophies}')
        value = input('Confirm: (Y/n)')
        if value and value.upper() == 'N':
            raise StopProcessing

        Trophy.objects.bulk_create([Trophy(name=e) for e in trophies])
        dfs[COMPUTED_TROPHY] = dfs.apply(lambda x: self.__get_trophy(x[COLUMN_NAME]), axis=1)
