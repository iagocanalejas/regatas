import logging
from abc import ABC

from digesters.scrappers import Scrapper

logger = logging.getLogger(__name__)

ARC_V1 = 'v1'
ARC_V2 = 'v2'


class ARCScrapper(Scrapper, ABC):
    _registry = {}

    _excluded_ids = []
    _is_female: bool
    _year: int

    DATASOURCE: str = 'arc'

    def __init_subclass__(cls, **kwargs):
        version = kwargs.pop('version')
        super().__init_subclass__(**kwargs)
        cls._registry[version] = cls

    def __new__(cls, year: int, is_female: bool = False, **kwargs):  # pragma: no cover
        version = ARC_V1 if year < 2009 else ARC_V2
        subclass = cls._registry[version]
        final_obj = object.__new__(subclass)

        final_obj._is_female = is_female
        final_obj._year = year

        return final_obj
