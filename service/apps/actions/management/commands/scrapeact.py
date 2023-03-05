import logging
import time
from typing import List

from django.core.management import BaseCommand

from apps.actions.digesters import ScrappedItem
from apps.actions.digesters import ACTScrapper
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import data from ACT web'

    def add_arguments(self, parser):
        parser.add_argument('--year', default=None, type=int, help='')
        parser.add_argument('--female', action='store_true', default=False)
        parser.add_argument('--all', action='store_true', default=False)

    def handle(self, *args, **options):
        if not options['year'] and not options['all']:
            raise Exception

        scrapper = ACTScrapper(is_female=options['female'])
        if options['all']:
            i = 2009 if options['female'] else 2003
            items: List[ScrappedItem] = []
            while True:
                try:
                    items.extend(scrapper.scrap(year=i))
                except StopProcessing:
                    break

                i += 1
                time.sleep(5)

            scrapper.save(items)

        if options['year']:
            scrapper.save(
                list(scrapper.scrap(year=options['year'])),
                file_name=f'{options["year"]}.csv',
            )
