import logging
import time
from typing import List

from django.core.management import BaseCommand

from apps.actions.management.utils import ScrappedItem, save_items
from apps.actions.management.scrappers import ARCScrapper
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

            save_items(items, file_name=ARCScrapper.DATASOURCE)

        if options['year']:
            scrapper = ARCScrapper(is_female=options['female'], year=int(options['year']))
            save_items(list(scrapper.scrap()), file_name=f'{options["year"]}.csv')
