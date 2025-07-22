from django.db.models import Q, QuerySet

from apps.races.models import Race
from pyutils.strings import remove_conjunctions, remove_symbols, whitespaces_clean


# TODO: refactor this to remove the builder pattern
class RaceFilters:
    _FILTERS_MAP = {
        "year": "date__year",
        "day": "day",
        "trophy": "trophy_id",
        "flag": "flag_id",
        "league": "league_id",
        "participant": "participant__club_id",
        "metadata": "metadata__datasource__contains",
    }
    _SORTING_MAP = {
        "type": ["type"],
        "date": ["date"],
        "name": ["trophy__name", "flag__name"],
        "league": ["league__name"],
    }
    _DEFAULT_SORTING = ["date"]

    def __init__(self, queryset: QuerySet[Race]):
        self.sorting = self._DEFAULT_SORTING
        self.keywords = None
        self.filters = {}
        self.queryset = queryset

    def set_keywords(self, keywords: str | None) -> "RaceFilters":
        if keywords:
            self.keywords = whitespaces_clean(remove_conjunctions(remove_symbols(keywords)))
        return self

    def set_filters(self, filters: dict) -> "RaceFilters":
        self.filters = {
            self._FILTERS_MAP[key]: value for key, value in filters.items() if key in self._FILTERS_MAP.keys()
        }
        return self

    def add_filter(self, key: str, value: str) -> "RaceFilters":
        self.filters[self._FILTERS_MAP[key]] = value
        return self

    def set_sorting(self, sort_by: str | None) -> "RaceFilters":
        if not sort_by or sort_by.replace("-", "") not in self._SORTING_MAP.keys():
            self.sorting = self._DEFAULT_SORTING
            return self

        desc, sort_by = "-" in sort_by, sort_by.replace("-", "")
        self.sorting = [f"-{e}" for e in self._SORTING_MAP[sort_by]] if desc else self._SORTING_MAP[sort_by]
        return self

    # noinspection DuplicatedCode
    def build_query(self) -> QuerySet[Race]:
        queryset = self.queryset.filter(**self.filters)
        if self.keywords:
            queryset = queryset.filter(
                Q(trophy__isnull=False, trophy__name__icontains=self.keywords)
                | Q(flag__isnull=False, flag__name__icontains=self.keywords)
                | Q(league__isnull=False, league__name__icontains=self.keywords)
                | Q(sponsor__isnull=False, sponsor__icontains=self.keywords)
                | Q(town__isnull=False, town__icontains=self.keywords)
            )

        queryset = queryset.order_by(*self.sorting)

        return queryset
