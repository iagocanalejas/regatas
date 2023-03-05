import logging
import os
from typing import List

from django.core.management import BaseCommand

from apps.actions.digesters import ScrappedItem
from apps.actions.digesters import ImageOCR

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Tries to import data from an image'
    optimize: bool = False

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)
        parser.add_argument('--datasource', type=str)
        parser.add_argument('--plot', action='store_true', default=False)

    def handle(self, *args, **options):
        items: List[ScrappedItem] = []
        scrapper: ImageOCR = ImageOCR(source=options['datasource'], allow_plot=options['plot'])
        scrapper.set_language('es_ES.utf8')
        for file in self._path_files(options['path']):
            items.extend(scrapper.digest(path=file))

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
