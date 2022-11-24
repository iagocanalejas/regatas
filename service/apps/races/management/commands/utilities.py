import logging

from django.core.management import BaseCommand

from apps.entities.models import LEAGUE_GENDERS
from apps.races.models import Trophy, Flag, Race
from utils.synonyms import lemmatize

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Multiple utilities for data fixing'

    def add_arguments(self, parser):
        parser.add_argument('--duplicates', action='store_true', default=False)
        parser.add_argument('--lemmatize', action='store_true', default=False)
        parser.add_argument('--editions', action='store_true', default=False)
        parser.add_argument('--all', action='store_true', default=False)

    def handle(self, *args, **options):
        if options['duplicates']:
            self.__find_duplicates(Trophy)
            self.__find_duplicates(Flag)
        if options['lemmatize']:
            self.__lemmatize(Trophy, everything=('all' in options))
            self.__lemmatize(Flag, everything=('all' in options))
        if options['editions']:
            self._missing_editions()

    @staticmethod
    def __find_duplicates(model):
        items = model.objects.filter(verified=False)
        for item in items:
            matches = model.objects.exclude(id=item.pk).filter(tokens__contains=item.tokens)
            if len(matches):
                logger.info(f'{model.__name__}: {item} -> {matches}')

    @staticmethod
    def __lemmatize(model, everything: bool = False):
        items = model.objects.all() if everything else model.objects.filter(tokens__len=0)
        for item in items:
            item.tokens = list(lemmatize(item.name))
            item.save()

    def _missing_editions(self):
        trophies = Trophy.objects.all()
        for trophy in trophies:
            races = Race.objects.filter(trophy=trophy) \
                .order_by('trophy_edition')

            options = LEAGUE_GENDERS + [None]

            for option in options:
                trophy_editions = [
                    r.trophy_edition for r in races
                    if (r.league and r.league.gender == option) or (not r.league and r.gender == option)
                ]
                missing = self.__missing_elements(trophy_editions)
                if missing:
                    logger.info(f'{trophy}: {missing}')

    @staticmethod
    def __missing_elements(items):
        if len(items) < 2:
            return
        start, end = items[0], items[-1]
        return sorted(set(range(start, end + 1)).difference(items))
