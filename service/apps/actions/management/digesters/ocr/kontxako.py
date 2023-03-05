import logging
import os
import re
from datetime import date, datetime
from typing import List, Optional

import cv2
from pandas import DataFrame, Series

from ai_django.ai_core.utils.strings import whitespaces_clean
from apps.actions.management.digesters._item import ScrappedItem
from apps.actions.management.digesters.ocr._image import ImageOCR
from apps.entities.normalization import normalize_club_name
from apps.participants.normalization import normalize_lap_time
from utils.synonyms import TIME_TRIAL_SYNONYMS, FEMALE_SYNONYMS, CLASSIFICATION_SYNONYMS

logger = logging.getLogger(__name__)


class ImageOCRKontxako(ImageOCR, source='kontxako'):
    DATASOURCE = 'kontxako'

    def digest(self, path: str, optimize: bool = False) -> List[ScrappedItem]:
        logger.info(f'processing {path}')

        img = cv2.imread(path, 0)
        img_vh, img_bin = self._retrieve_image_vh(img)

        details = self.get_parsed_image(img_bin=img_bin)
        if not self.get_name(details) or not self.get_date(details):
            details = self.get_parsed_image(img_bin=img_bin, optimize=True)
        details = details.upper() if details else details

        name = self.get_name(details)
        t_date = self.get_date(details)
        town = self.get_town(details)
        organizer = self.get_organizer(details)
        gender = self.get_gender(details)
        race_lanes = self.get_race_lanes(details)
        race_laps = self.get_race_laps(details)
        if not name or not t_date:
            logger.error(f'unable to process: {path}')
            return []

        df = self.get_image_dataframe(img=img, img_vh=img_vh, optimize=optimize)
        df.reset_index(drop=True, inplace=True)

        itx = 0
        for _, row in df.iterrows():
            club_name = self.get_club_name(row)
            yield ScrappedItem(
                name=name,
                trophy_name=self.normalized_name(name),
                edition=1,
                day=1,
                t_date=t_date,
                town=town,
                gender=gender,
                league=None,
                organizer=organizer,
                club_name=club_name,
                participant=self.normalized_club_name(club_name),
                series=(itx // race_lanes) + 1,
                lane=self.get_lane(row),
                laps=self.get_laps(row),
                race_id=os.path.basename(path),
                url=None,
                datasource=self.DATASOURCE,
                race_laps=race_laps,
                race_lanes=race_lanes
            )
            itx += 1

    @staticmethod
    def get_edition(name: str, **kwargs) -> int:
        raise NotImplementedError

    def get_gender(self, soup, **kwargs) -> Optional[str]:
        return 'FEMENINA' if any(x in soup for x in FEMALE_SYNONYMS()) else 'MASCULINA'

    def get_name(self, soup: str, **kwargs) -> str:
        return 'BANDERA DE LA CONCHA (CLASIFICATORIA)' if any(x in soup for x in TIME_TRIAL_SYNONYMS()) else 'BANDERA DE LA CONCHA'

    def normalized_name(self, name: str, **kwargs) -> str:
        return name

    def get_day(self, soup: str, **kwargs) -> int:
        # TODO: this does not work
        return 2 if any(x in soup for x in CLASSIFICATION_SYNONYMS()) else 1

    def get_date(self, soup: str, **kwargs) -> Optional[date]:
        for line in soup.split('\n'):
            match = re.findall(r'\d{1,2}/\d{2}/20\d{2}', whitespaces_clean(line))
            if not len(match):
                match = re.findall(r'20\d{2}/\d{2}/\d{2}', whitespaces_clean(line))
            if len(match):
                try:
                    return datetime.strptime(match[0], '%d/%m/%Y')
                except ValueError:
                    try:
                        return datetime.strptime(match[0], '%Y/%m/%d')
                    except ValueError:
                        pass

    def get_town(self, soup, **kwargs) -> Optional[str]:
        return 'KONTXAKO BADIA'

    def get_organizer(self, soup, **kwargs) -> Optional[str]:
        return 'DONOSTIA KULTURA'

    def get_club_name(self, soup, **kwargs) -> str:
        return soup[2]

    def normalized_club_name(self, name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_lane(self, soup, **kwargs) -> int:
        return soup[4]

    def get_laps(self, soup, **kwargs) -> List[str]:
        return [t.isoformat() for t in [normalize_lap_time(t) for t in soup.iloc[6:]] if t]

    def get_race_lanes(self, soup, **kwargs) -> int:
        return 1 if any(x in soup for x in TIME_TRIAL_SYNONYMS()) else 4

    def get_race_laps(self, soup, **kwargs) -> int:
        return 2

    def get_series(self, soup, **kwargs) -> int:
        raise NotImplementedError

    def get_league(self, soup, trophy: str, **kwargs) -> Optional[str]:
        raise NotImplementedError

    ####################################################
    #              DATAFRAME PROCESSING                #
    ####################################################
    __PROCESSED = []

    def _should_process(self, row: Series) -> bool:
        if row[2] in self.__PROCESSED:
            return False
        for _, col in row.items():
            if len(re.findall(r'\d+:\d+,\d+', col)):
                self.__PROCESSED.append(row[2])
                return True
        return False

    def clean_dataframe(self, df: DataFrame) -> DataFrame:
        df = df.applymap(whitespaces_clean)
        df.drop(df.columns[[0]], axis=1, inplace=True)
        df[6] = df[6].map(lambda x: x.split(' ')[-1])
        df[7] = df[7].map(lambda x: x.split(' ')[-1])

        remove = []
        for index, row in df.iterrows():
            if not self._should_process(row):
                remove.append(index)
        df.drop(remove, inplace=True)

        self.__PROCESSED = []
        return df
