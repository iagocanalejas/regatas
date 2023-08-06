import datetime
from ast import literal_eval
from datetime import time
from typing import Optional, Dict, Tuple

import inquirer
from pandas import Series

from rscraping import Datasource
from rscraping.data.functions import is_play_off

from apps.actions.management.commands.validate import *
from apps.participants.models import Participant, Penalty
from apps.participants.services import ParticipantService
from apps.races.models import Flag
from apps.races.services import RaceService, FlagService
from apps.schemas import MetadataBuilder
from utils.choices import RACE_CONVENTIONAL, RACE_TIME_TRIAL, GENDER_FEMALE, GENDER_MALE
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)

_KNOWN_MAPPINGS = {
    'BANDEIRA XUNTA DE GALICIA': ['CAMPEONATO GALEGO DE TRAINERAS'],
}


class Command(BaseCommand):
    help = 'Import CSV file into the DB'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)
        parser.add_argument('--no-input', action='store_true', default=False)
        parser.add_argument('--only-validate', action='store_true', default=False)

    def handle(self, *args, **options):
        for file in options['path']:
            validate_file(file, manual=not options['no_input'])
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

            self.digest(dfs, manual=not options['no_input'])

    ####################################################
    #                  DIGEST METHODS                  #
    ####################################################

    def digest(self, dfs: DataFrame, manual: bool = False):
        # create missing trophies/flags
        missing_trophies = dfs.loc[dfs[COMPUTED_TROPHY].isnull() & dfs[COMPUTED_FLAG].isnull()][COLUMN_TROPHY].unique()
        if len(missing_trophies) > 0:
            if not manual:
                raise StopProcessing(f'missing: {missing_trophies}')
            self._create_trophy_or_flag(dfs, missing_trophies)

        # check all missing trophies/flags where created
        if len(dfs.loc[dfs[COMPUTED_TROPHY].isnull() & dfs[COMPUTED_FLAG].isnull()][COLUMN_TROPHY].unique()) > 0:
            raise StopProcessing

        # create or get all races
        for race_id in dfs[COLUMN_RACE_ID].unique():
            logger.debug(f'processing race {race_id}')
            self._get_race_or_create(dfs, dfs.loc[(dfs[COLUMN_RACE_ID] == race_id)].iloc[0])

        for index, row in dfs.iterrows():
            logger.debug(f'processing row {index}')
            self._create_or_update_participant(row)

    @staticmethod
    def get_race_lanes(dfs: DataFrame, row: Series) -> int:
        lanes = row[COLUMN_RACE_LANES]
        if not lanes:
            lanes = dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LANE].max()
        if lanes > 5:
            logger.warning(f'race found with more than 5 lanes: {row[COLUMN_RACE_ID]}')
        return lanes

    @staticmethod
    def get_race_laps(dfs: DataFrame, row: Series) -> int:
        laps = row[COLUMN_RACE_LAPS]
        if not laps:
            laps = max([len(e) for e in dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LAPS]])
        if laps > 6:
            logger.warning(f'race found with more than 6 laps: {row[COLUMN_RACE_ID]}')
        return laps

    @staticmethod
    def get_race_type(dfs: DataFrame, row: Series) -> str:
        lanes = row[COLUMN_RACE_LANES]
        if not lanes:
            lanes = dfs.loc[dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]][COLUMN_LANE].max()
        return RACE_TIME_TRIAL if lanes == 1 else RACE_CONVENTIONAL

    @staticmethod
    def is_disqualified(row: Series) -> bool:
        return row[COLUMN_DISQUALIFIED] if COLUMN_DISQUALIFIED in row else False

    ####################################################
    #                 DATAFRAME METHODS                #
    ####################################################

    def _prepare_dataframe(self, dfs: DataFrame) -> DataFrame:
        # fill optional columns
        dfs[COLUMN_TROPHY] = dfs[COLUMN_TROPHY] if COLUMN_TROPHY in dfs else dfs[COLUMN_NAME]
        dfs[COLUMN_CLUB] = dfs[COLUMN_CLUB] if COLUMN_CLUB in dfs else dfs[COLUMN_CNAME]

        # remove leagues for play-off races
        dfs[COLUMN_LEAGUE] = dfs.apply(lambda x: self._get_league(x[COLUMN_LEAGUE]) if not is_play_off(x[COLUMN_TROPHY]) else None, axis=1)

        # find already existing data
        dfs[COMPUTED_TROPHY] = dfs.apply(lambda x: self._get_trophy(x[COLUMN_TROPHY]), axis=1)
        dfs[COMPUTED_FLAG] = dfs.apply(lambda x: self._get_flag(x[COLUMN_TROPHY]), axis=1)
        dfs[COMPUTED_RACE] = dfs.apply(lambda x: None, axis=1)
        dfs[COMPUTED_PARTICIPANT] = dfs.apply(lambda x: self._get_club(x[COLUMN_CLUB]), axis=1)
        dfs[COLUMN_ORGANIZER] = dfs.apply(lambda x: self._get_organizer(x[COLUMN_ORGANIZER]), axis=1)
        dfs[COLUMN_GENDER] = dfs.apply(lambda x: x[COLUMN_LEAGUE].gender if x[COLUMN_LEAGUE] else x[COLUMN_GENDER], axis=1)

        date_pairs = self._date_pairs(dfs.loc[dfs[COLUMN_DAY] == 1][COLUMN_DATE].unique())
        for start, end in date_pairs:
            self._fix_days(dfs, start, end, column=COMPUTED_TROPHY)
            self._fix_days(dfs, start, end, column=COMPUTED_FLAG)

        return dfs

    @staticmethod
    def _fix_days(dfs: DataFrame, start: datetime.date, end: datetime.date, column: str):
        """
        Tries to fix two-day races with wrong 'day' columns
        """
        for _, row in dfs.loc[(dfs[COLUMN_DATE] == start) & (dfs[COLUMN_DAY] == 1)].iterrows():
            matches = dfs.loc[(dfs[COLUMN_DATE] == end) & (dfs[column] == row[column]) & (dfs[COLUMN_DAY] == 1) &
                              ((row[COLUMN_LEAGUE] is None) | (dfs[COLUMN_LEAGUE] == row[COLUMN_LEAGUE])) &
                              ((row[COLUMN_GENDER] is None) | (dfs[COLUMN_GENDER] == row[COLUMN_GENDER]))]

            if not matches.empty:
                logger.info(f'updating day for {end}:: {matches.index}')
                dfs.loc[matches.index, [COLUMN_DAY]] = 2

    @staticmethod
    def _date_pairs(dates: List[datetime.date]) -> List[Tuple[datetime.date, datetime.date]]:
        """
        Returns a list of sorted date pairs trying
        """
        pairs = []

        dates = sorted(dates)
        start = dates[0]
        for i in range(1, len(dates)):
            if dates[i] == start + datetime.timedelta(days=1):
                pairs.append((start, dates[i]))
            start = dates[i]

        return pairs

    ####################################################
    #                DB ACCESS METHODS                 #
    ####################################################

    def _get_league(self, league: str) -> Optional[League]:
        if not league:
            return None

        # try to find in the memory cache
        cached = self.cache_get('leagues', league)
        if cached:
            return cached

        found_league = LeagueService.get_by_name(league)
        self.cache_put('leagues', league, found_league)
        return found_league

    def _get_club(self, club: str) -> Entity:
        # try to find in the memory cache
        cached = self.cache_get('clubs', club)
        if cached:
            return cached

        # search in database
        found_club = EntityService.get_closest_club_by_name(club)
        self.cache_put('clubs', club, found_club)
        return found_club

    def _get_organizer(self, club: Optional[str]) -> Optional[Entity]:
        if not club:
            return None

        # try to find in the memory cache
        cached = self.cache_get('clubs', club)
        if cached:
            return cached

        # search in database
        found_organizer = EntityService.get_closest_by_name_type(club)
        self.cache_put('clubs', club, found_organizer)
        return found_organizer

    # noinspection DuplicatedCode
    def _get_trophy(self, trophy: str) -> Optional[Trophy]:
        for k, v in _KNOWN_MAPPINGS.items():
            if trophy in v or any(part in trophy for part in v):
                trophy = k
                break

        # try to find in the memory cache
        cached = self.cache_get('trophies', trophy)
        if cached:
            return cached

        # search in database
        try:
            found_trophy = TrophyService.get_closest_by_name(trophy)
            self.cache_put('trophies', trophy, found_trophy)
            return found_trophy
        except Trophy.DoesNotExist:
            return None

    def _get_flag(self, flag: str) -> Optional[Flag]:
        for k, v in _KNOWN_MAPPINGS.items():
            if flag in v or any(part in flag for part in v):
                flag = k
                break

        # try to find in the memory cache
        cached = self.cache_get('flags', flag)
        if cached:
            return cached

        # search in database
        try:
            found_flag = FlagService.get_closest_by_name(flag)
            self.cache_put('flags', flag, found_flag)
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
        metadata = MetadataBuilder() \
            .ref_id(row[COLUMN_RACE_ID]) \
            .datasource_name(Datasource(row[COLUMN_DATASOURCE]))
        if COLUMN_URL in row and row[COLUMN_URL]:
            metadata = metadata.values('details_page', row[COLUMN_URL])
            metadata = metadata.gender(GENDER_FEMALE if row[COLUMN_GENDER] else GENDER_MALE)

        race = Race(
            laps=self.get_race_laps(dfs, row),
            lanes=self.get_race_lanes(dfs, row),
            town=row[COLUMN_TOWN],
            type=self.get_race_type(dfs, row),
            date=row[COLUMN_DATE],
            day=row[COLUMN_DAY],
            cancelled=row[COLUMN_CANCELLED] if COLUMN_CANCELLED in row else False,
            race_name=row[COLUMN_NAME],  # un-normalized race name
            trophy=row[COMPUTED_TROPHY],
            trophy_edition=row[COLUMN_EDITION] if row[COMPUTED_TROPHY] else None,
            flag=row[COMPUTED_FLAG],
            flag_edition=row[COLUMN_EDITION] if row[COMPUTED_FLAG] else None,
            league=row[COLUMN_LEAGUE],
            modality=row[COLUMN_MODALITY],
            organizer=row[COLUMN_ORGANIZER],
            metadata={'datasource': [metadata.build()]},
        )
        created, db_race = RaceService.get_race_or_create(race)
        if not created:
            self._compare(race, db_race)

            # fill data sources if we are updating a race
            if not any(x['datasource_name'] == row[COLUMN_DATASOURCE] for x in db_race.metadata["datasource"]):
                db_race.metadata['datasource'].append(race.metadata['datasource'].pop())
                db_race.save()

        dfs[COMPUTED_RACE].mask((dfs[COLUMN_RACE_ID] == row[COLUMN_RACE_ID]), db_race, inplace=True)

    def _create_or_update_participant(self, row: Series):
        participant = Participant(
            club_name=row[COLUMN_CNAME],  # un-normalized used club name
            club=row[COMPUTED_PARTICIPANT],
            race=row[COMPUTED_RACE],
            distance=row[COLUMN_DISTANCE],
            laps=row[COLUMN_LAPS],
            lane=row[COLUMN_LANE],
            series=row[COLUMN_SERIES],
            gender=row[COLUMN_GENDER],
            category=row[COLUMN_CATEGORY],
        )
        created, db_participant = ParticipantService.get_participant_or_create(participant, maybe_branch=True)
        if not created:
            self._compare(participant, db_participant)

        if self.is_disqualified(row):
            penalty = Penalty.objects.create(disqualification=True, participant=db_participant)
            logger.info(f'created penalty {penalty}')

    @staticmethod
    def _compare(e1: Race | Participant, e2: Race | Participant):
        ignored_keys = ['id', 'metadata', 'creation_date', 'distance', 'club_name', 'race_name']
        keys = [k for k in e1.__dict__.keys() if not k.startswith('_') and k not in ignored_keys]
        for k in keys:
            if e1.__dict__[k] != e2.__dict__[k]:
                logger.warning(f'mismatch({k}) between: {e1}({e1.__dict__[k]}) and {e2}({e2.__dict__[k]})')

    ####################################################
    #                   CACHE METHODS                  #
    ####################################################
    _CACHE: Dict[str, Dict[str, League | Entity | Trophy | Flag]] = {
        'leagues': {},
        'clubs': {},
        'trophies': {},
        'flags': {},
    }

    def cache_get(self, ttype: str, key: str) -> League | Entity | Trophy | Flag:
        return getattr(self._CACHE[ttype], key, None)

    def cache_put(self, ttype: str, key: str, value: League | Entity | Trophy | Flag):
        self._CACHE[ttype][key] = value
