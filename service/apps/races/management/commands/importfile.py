import datetime
import itertools
from ast import literal_eval
from datetime import time, date
from typing import Optional, Dict, Tuple

import inquirer
from pandas import Series

from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from apps.races.management.commands.validate import *
from apps.races.models import Flag
from apps.races.services import RaceService, FlagService
from digesters import Digester
from utils.choices import RACE_CONVENTIONAL, RACE_TIME_TRIAL
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)

_KNOWN_MAPPINGS = {
    'BANDEIRA XUNTA DE GALICIA': ['CAMPEONATO GALEGO DE TRAINERAS'],
}


# TODO: create getters
class Command(BaseCommand, Digester):
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
        for file in options['path']:
            validate_file(file, manual=options['manual'])
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

            self.digest(dfs, manual=options['manual'])

    ####################################################
    #                  DIGEST METHODS                  #
    ####################################################

    def digest(self, dfs: DataFrame, manual: bool = False, **kwargs):
        # create missing trophies/flags
        missing_trophies = dfs.loc[dfs[COMPUTED_TROPHY].isnull() & dfs[COMPUTED_FLAG].isnull()][COLUMN_TROPHY].unique()
        if len(missing_trophies) > 0:
            if not manual:
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

    def get_name(self, soup, **kwargs) -> str:
        pass

    def get_date(self, soup, **kwargs) -> date:
        pass

    @staticmethod
    def get_edition(name: str, **kwargs) -> int:
        pass

    def get_day(self, name: str, **kwargs) -> int:
        pass

    def get_modality(self, **kwargs) -> str:
        pass

    def get_league(self, soup, trophy: str, **kwargs) -> Optional[str]:
        pass

    def get_town(self, soup, **kwargs) -> Optional[str]:
        pass

    def get_organizer(self, soup, **kwargs) -> Optional[str]:
        pass

    def get_gender(self, **kwargs) -> str:
        pass

    def get_category(self, **kwargs) -> str:
        pass

    def get_club_name(self, soup, **kwargs) -> str:
        pass

    def get_lane(self, soup, **kwargs) -> int:
        pass

    def get_series(self, soup, **kwargs) -> int:
        pass

    def get_laps(self, soup, **kwargs) -> List[str]:
        pass

    def get_distance(self, **kwargs) -> int:
        pass

    def normalized_name(self, name: str, **kwargs) -> str:
        pass

    def normalized_club_name(self, name: str, **kwargs) -> str:
        pass

    def get_race_lanes(self, soup, **kwargs) -> int:
        pass

    def get_race_laps(self, soup, **kwargs) -> int:
        pass

    ####################################################
    #                 PRIVATE METHODS                  #
    ####################################################

    def _prepare_dataframe(self, dfs: DataFrame) -> DataFrame:
        # fill optional columns
        dfs[COLUMN_TROPHY] = dfs[COLUMN_TROPHY] if COLUMN_TROPHY in dfs else dfs[COLUMN_NAME]
        dfs[COLUMN_CLUB] = dfs[COLUMN_CLUB] if COLUMN_CLUB in dfs else dfs[COLUMN_CNAME]

        # remove leagues for play-off races
        dfs[COLUMN_LEAGUE] = dfs.apply(lambda x: x[COLUMN_LEAGUE] if not self.is_play_off(x[COLUMN_TROPHY]) else None, axis=1)

        # TODO: i'm here
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
    def _get_distance(row: Series) -> int:
        return row[COLUMN_DISTANCE]

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
            if menu.lower() == 'create trophy':
                new_name = inquirer.text(f'Rename trophy {name} to:')
                if new_name:
                    trophy = TrophyService.get_closest_by_name_or_create(name=new_name)
                else:
                    trophy = Trophy(name=name.upper())
                    trophy.save()
                    logger.info(f'created:: {trophy}')

                dfs[COMPUTED_TROPHY].mask(dfs[COLUMN_TROPHY] == t_name, trophy, inplace=True)
            elif menu.lower() == 'create flag':
                new_name = inquirer.text(f'Rename flag {name} to:')
                if new_name:
                    flag = FlagService.get_closest_by_name_or_create(name=new_name)
                else:
                    flag = Flag(name=name.upper())
                    flag.save()
                    logger.info(f'created:: {flag}')

                dfs[COMPUTED_FLAG].mask(dfs[COLUMN_TROPHY] == t_name, flag, inplace=True)
            else:
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
            distance=self._get_distance(row),
            lane=row[COLUMN_LANE],
            laps=row[COLUMN_LAPS],
            series=row[COLUMN_SERIES],
            disqualified=row[COLUMN_DISQUALIFIED] if COLUMN_DISQUALIFIED in row else False,
        )
        created, db_participant = ParticipantService.get_participant_or_create(participant)
        if not created:
            self._compare(participant, db_participant)

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
