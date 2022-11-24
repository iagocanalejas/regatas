import locale
import logging
import os
from typing import List

from django.core.management import BaseCommand

from scrappers import ImageScrapper, ScrappedItem

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Tries to import data from an image'
    optimize: bool = False

    def __init__(self):
        super().__init__()
        locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)
        parser.add_argument('--datasource', type=str)
        parser.add_argument('--optimize', action='store_true', default=False)

    def handle(self, *args, **options):
        assert options['path']

        items: List[ScrappedItem] = []
        scrapper: ImageScrapper = ImageScrapper(source=options['datasource'])
        for file in self._path_files(options['path']):
            items.extend(scrapper.scrap(path=file, optimize=options['optimize']))

        scrapper.save(items)

    @staticmethod
    def _valid_file(file: str) -> bool:
        _, extension = os.path.splitext(file)
        return extension.upper() in ['.JPG', '.JPEG', '.PNG']

    def _path_files(self, paths: List[str]) -> List[str]:
        files = []
        for path in paths:
            if os.path.isdir(path):
                [files.append(os.path.join(path, file)) for file in os.listdir(path)]
            else:
                files.append(path)

        return [f for f in files if self._valid_file(f)]
