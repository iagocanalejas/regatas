from abc import ABC

from apps.actions.datasource import Datasource
from apps.actions.management.scrappers import Scrapper


class ARCScrapper(Scrapper, ABC):
    _registry = {}

    _excluded_ids = []
    _is_female: bool
    _year: int

    def __init_subclass__(cls, **kwargs):
        version = kwargs.pop('version')
        super().__init_subclass__(**kwargs)
        cls._registry[version] = cls

    def __new__(cls, year: int, is_female: bool = False, **kwargs) -> 'ARCScrapper':  # pragma: no cover
        version = Datasource.ARCVersions.V1 if year < 2009 else Datasource.ARCVersions.V2
        subclass = cls._registry[version]
        final_obj = object.__new__(subclass)

        final_obj._is_female = is_female
        final_obj._year = year

        return final_obj
