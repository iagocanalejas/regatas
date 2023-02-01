import logging
import os
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import cv2
import numpy as np
from pandas import DataFrame, Series

from ai_django.ai_core.utils.strings import whitespaces_clean
from apps.entities.models import LEAGUE_GENDER_MALE, LEAGUE_GENDER_FEMALE
from apps.entities.normalization import normalize_club_name
from apps.races.normalization import normalize_trophy_name
from digesters._item import ScrappedItem
from digesters.ocr.image import ImageOCR, IMAGE_INFOREMO

logger = logging.getLogger(__name__)

_GENDERS = {
    LEAGUE_GENDER_MALE: ['MASCULINO'],
    LEAGUE_GENDER_FEMALE: ['FEMENINO'],
}


# noinspection Assert
class ImageOCRInforemo(ImageOCR, source=IMAGE_INFOREMO):
    __TEMP_NAME_TOWN_DATE = None

    DATASOURCE = IMAGE_INFOREMO

    def digest(self, path: str, optimize: bool = False) -> List[ScrappedItem]:
        assert os.path.isfile(path)
        logger.info(f'processing {path}')
        self.__TEMP_NAME_TOWN_DATE = None

        img = cv2.imread(path, 0)
        img_vh, img_bin = self._retrieve_image_vh(img)

        details = self.get_parsed_image(img_bin=img_bin)
        if not self.get_name(details) or not self.get_date(details):
            self.__TEMP_NAME_TOWN_DATE = None
            details = self.get_parsed_image(img_bin=img_bin, optimize=True)

        name = self.get_name(details)
        t_date = self.get_date(details)
        town = self.get_town(details)
        if not name or not t_date:
            logger.error(f'unable to process: {path}')
            return []

        df = self.get_image_dataframe(img=img, img_vh=img_vh, optimize=optimize)

        trophy_name = self.normalized_name(name)
        race_lanes = self.get_race_lanes(df)
        race_laps = self.get_race_laps(df)
        for itx, row in df.iterrows():
            club_name = self.get_club_name(row)
            yield ScrappedItem(
                name=name,
                trophy_name=trophy_name,
                edition=1,
                day=1,
                t_date=t_date,
                town=town,
                gender=self.get_gender(row),
                league=None,
                organizer=None,
                club_name=club_name,
                participant=self.normalized_club_name(club_name),
                series=self.get_series(row),
                lane=self.get_lane(row),
                laps=self.get_laps(row),
                race_id=os.path.basename(path),
                url=None,
                datasource=self.DATASOURCE,
                race_laps=race_laps,
                race_lanes=race_lanes
            )

    @staticmethod
    def get_edition(name: str, **kwargs) -> int:
        raise NotImplementedError

    def get_name(self, soup: str, **kwargs) -> Optional[str]:
        return self._retrieve_name_town_date(soup)[0]

    def get_gender(self, soup: Series, **kwargs) -> Optional[str]:
        gender = soup[2]
        for k, v in _GENDERS.items():
            if gender in v or any(part in gender for part in v):
                gender = k
                break
        return gender

    def normalized_name(self, name: str, **kwargs) -> str:
        return normalize_trophy_name(name, False)

    def get_date(self, soup: str, **kwargs) -> Optional[date]:
        return self._retrieve_name_town_date(soup)[2]

    def get_town(self, soup: str, **kwargs) -> Optional[str]:
        return self._retrieve_name_town_date(soup)[1]

    def get_club_name(self, soup: Series, **kwargs) -> str:
        return soup[1]

    def normalized_club_name(self, name: str, **kwargs) -> str:
        return normalize_club_name(name)

    def get_lane(self, soup: Series, **kwargs) -> int:
        return soup[4]

    def get_series(self, soup: Series, **kwargs) -> int:
        return soup[3]

    def get_laps(self, soup: Series, **kwargs) -> List[str]:
        return [t.isoformat() for t in [self.normalize_time(t) for t in soup.iloc[4:]] if t]

    def get_race_lanes(self, df: DataFrame, **kwargs) -> int:
        return max(row[4] for _, row in df.iterrows())

    def get_race_laps(self, df: DataFrame, **kwargs) -> int:
        return len(df.columns) - 4

    def get_organizer(self, soup: np.ndarray, **kwargs) -> Optional[str]:
        raise NotImplementedError

    def get_league(self, soup: np.ndarray, trophy: str, **kwargs) -> Optional[str]:
        raise NotImplementedError

    def get_day(self, name: str, **kwargs) -> int:
        raise NotImplementedError

    ####################################################
    #              DATAFRAME PROCESSING                #
    ####################################################
    @staticmethod
    def _should_process(row: Series) -> bool:
        for _, col in row.items():
            if col in ['FEMENINO', 'MASCULINO']:
                return True
        return False

    def clean_dataframe(self, df: DataFrame) -> DataFrame:
        df = df.applymap(whitespaces_clean)
        df.drop(df.columns[[0, len(df.columns) - 1]], axis=1, inplace=True)

        remove = []
        for index, row in df.iterrows():
            if not self._should_process(row):
                remove.append(index)
        df.drop(remove, inplace=True)

        return df

    ####################################################
    #                  DATA RETRIEVAL                  #
    ####################################################

    def _retrieve_name_town_date(self, details: str) -> Tuple[Optional[str], Optional[str], Optional[date]]:
        if self.__TEMP_NAME_TOWN_DATE:
            return self.__TEMP_NAME_TOWN_DATE

        t_date = name = town = None
        for line in details.split('\n'):
            if name and town and t_date:
                break

            if not t_date:
                match = re.findall(r'\d{1,2} [a-zA-ZñÑ]+ 20\d{2}', whitespaces_clean(line))
                if len(match):
                    try:
                        t_date = datetime.strptime(match[0], '%d %B %Y')
                        continue
                    except ValueError:
                        pass
            if not name:
                match = re.match(r'^[a-zA-ZñÑ ]+$', whitespaces_clean(line))
                if match:
                    possible_name = match.group(0)
                    name = possible_name if len(possible_name) > 5 else None
                    continue
            if name and not town:
                match = re.match(r'^[a-zA-ZñÑ ]+$', whitespaces_clean(line))
                if match:
                    possible_town = match.group(0)
                    town = possible_town if len(possible_town) > 4 else None

        self.__TEMP_NAME_TOWN_DATE = name, town, (t_date.date() if t_date else None)
        return self.__TEMP_NAME_TOWN_DATE
