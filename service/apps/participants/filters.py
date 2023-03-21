from typing import Optional, Dict, List

from django.db.models import QuerySet, Q
from django.db.models.expressions import RawSQL

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_conjunctions, remove_symbols
from apps.participants.models import Participant


class ParticipantFilters:
    _FILTERS_MAP = {
        'year': 'race__date__year',
        'trophy': 'race__trophy_id',
        'flag': 'race__flag_id',
        'league': 'race__league_id',
        'gender': 'gender__iexact',
        'category': 'category__iexact',
    }
    _SORTING_MAP = {
        'type': ['race__type'],
        'date': ['race__date'],
        'name': ['race__trophy__name', 'race__flag__name'],
        'league': ['race__league__name'],
        'category': ['category', 'gender'],
        'speed': [],  # in-memory case
    }
    _DEFAULT_SORTING = ['race__date']

    def __init__(self, queryset: QuerySet[Participant]):
        self.sorting = self._DEFAULT_SORTING
        self.keywords = None
        self.filters = {}
        self.queryset = queryset

    def set_keywords(self, keywords: Optional[str]) -> 'ParticipantFilters':
        if keywords:
            self.keywords = whitespaces_clean(remove_conjunctions(remove_symbols(keywords)))
        return self

    def set_filters(self, filters: Dict) -> 'ParticipantFilters':
        self.filters = {self._FILTERS_MAP[key]: value for key, value in filters.items() if key in self._FILTERS_MAP.keys()}
        return self

    def add_filter(self, key: str, value: str) -> 'ParticipantFilters':
        self.filters[self._FILTERS_MAP[key]] = value
        return self

    def set_sorting(self, sort_by: Optional[str]) -> 'ParticipantFilters':
        if not sort_by or sort_by.replace('-', '') not in self._SORTING_MAP.keys():
            self.sorting = self._DEFAULT_SORTING
            return self

        desc, sort_by = '-' in sort_by, sort_by.replace('-', '')
        self.sorting = [f'-{e}' for e in self._SORTING_MAP[sort_by]] if desc else self._SORTING_MAP[sort_by]
        return self

    @staticmethod
    def sort_by_speed(queryset: QuerySet[Participant], reverse: bool) -> List[Participant]:
        # in-memory sort
        elements = list(
            queryset.filter(laps__len__gt=0).annotate(time=RawSQL('participant.laps[array_length(participant.laps, 1)]', ())).all()
        )
        elements.sort(
            key=lambda p: p.distance / ((p.time.minute * 60) + p.time.second + (p.time.microsecond / 100000)), reverse=reverse
        )
        return elements

    # noinspection DuplicatedCode
    def build_query(self) -> QuerySet[Participant]:
        queryset = self.queryset.filter(**self.filters)
        if self.keywords:
            queryset = queryset.filter(
                Q(race__trophy__isnull=False, race__trophy__name__unaccent__icontains=self.keywords)
                | Q(race__flag__isnull=False, race__flag__name__unaccent__icontains=self.keywords)
                | Q(race__league__isnull=False, race__league__name__unaccent__icontains=self.keywords)
                | Q(race__sponsor__isnull=False, race__sponsor__unaccent__icontains=self.keywords)
                | Q(race__town__isnull=False, race__town__unaccent__icontains=self.keywords)
            )

        queryset = queryset.order_by(*self.sorting)

        return queryset
