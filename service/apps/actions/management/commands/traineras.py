import logging

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from apps.actions.datasource import Datasource
from apps.entities.models import Entity
from apps.entities.normalization import normalize_club_name
from apps.schemas import MetadataBuilder
from utils.choices import ENTITY_CLUB

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    HEADERS = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Cache-Control': 'max-age=0'
    }

    def handle(self, *args, **options):
        for i in range(1, 9):
            url = f"https://traineras.es/clubes?page={i}"
            response = requests.get(url=url, headers=self.HEADERS)
            soup = BeautifulSoup(response.text, 'html5lib')

            for card in soup.find_all('div', {'class': 'col-lg-2 col-md-3 col-sm-4 col-xs-6 mt-5'}):
                name = card.find('a').text
                url = card.find('a')['href']
                ref_id = url.split('/')[-1]

                exists = Entity.objects.filter(metadata__datasource__contains=[{
                    "datasource_name": Datasource.TRAINERAS,
                    "ref_id": str(ref_id),
                }]).exists()

                if exists:
                    continue

                entity = Entity(
                    name=name,
                    normalized_name=normalize_club_name(name) or name,
                    type=ENTITY_CLUB,
                    symbol='TODO',
                    metadata={'datasource': [
                        MetadataBuilder().ref_id(ref_id).datasource_name(Datasource.TRAINERAS).values("details_page", url).build()
                    ]},
                )
                entity.save()
