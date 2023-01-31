import logging
import time
from typing import List

from django.core.management import BaseCommand

from digest.scrappers import ScrappedItem, ARCScrapper
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import data from ACT web'

    def add_arguments(self, parser):
        parser.add_argument('--year', default=None, type=int, help='')
        parser.add_argument('--female', action='store_true', default=False)
        parser.add_argument('--all', action='store_true', default=False)

    def handle(self, *args, **options):
        assert options['year'] or options['all']

        if options['all']:
            i = 2018 if options['female'] else 2006
            items: List[ScrappedItem] = []
            while True:
                try:
                    items.extend(ARCScrapper(is_female=options['female'], year=i).scrap())
                except StopProcessing:
                    break

                i += 1
                time.sleep(2)

            # we can use any scrapper for this
            ARCScrapper(is_female=options['female'], year=i).save(items)

        if options['year']:
            scrapper = ARCScrapper(is_female=options['female'], year=int(options['year']))
            scrapper.save(list(scrapper.scrap()), file_name=f'{options["year"]}.csv')
