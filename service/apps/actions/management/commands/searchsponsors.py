import logging
from typing import List

from django.core.management import BaseCommand
from django.db.models import ObjectDoesNotExist

from apps.races.models import Flag, Trophy
from apps.races.services import FlagService, TrophyService
from pyutils.lists import flatten
from pyutils.strings import normalize_synonyms, remove_conjunctions, remove_symbols, whitespaces_clean
from rscraping import SYNONYMS, Client, Datasource, lemmatize
from rscraping.data.functions import is_play_off
from rscraping.data.models import RaceName
from rscraping.data.normalization import normalize_name_parts, normalize_race_name

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument("year", default=None, type=int, help="")
        parser.add_argument("--datasource", type=str, help="Datasource from where to retrieve.")
        parser.add_argument("--female", action="store_true", default=False)
        parser.add_argument("--all", action="store_true", default=False)

    def handle(self, *_, **options):
        logger.info(f"{options}")

        year, datasource, is_female, do_all = options["year"], options["datasource"], options["female"], options["all"]
        if datasource and not Datasource.has_value(datasource):
            raise ValueError(f"invalid {datasource=}")
        if not year and not do_all:
            raise ValueError("missing param 'year' | 'all'")
        if not datasource and not do_all:
            raise ValueError("missing param 'datasource' | 'all'")

        items: List[RaceName] = []
        if do_all:
            for d in [Datasource.ACT, Datasource.ARC, Datasource.LGT]:
                client = Client(source=d, is_female=is_female)  # type: ignore
                items.extend(client.get_race_names_by_year(year, is_female=is_female))
        else:
            client = Client(source=Datasource(datasource), is_female=is_female)  # type: ignore
            items.extend(client.get_race_names_by_year(year, is_female=is_female))

        filtered_items = []
        for item in items:
            names = normalize_name_parts(normalize_race_name(item.name, is_female=is_female))
            for normalized_name, _ in names:
                if not normalized_name or is_play_off(normalized_name):
                    continue
                logger.info(f"searching DB for {normalized_name=}")
                try:
                    FlagService.get_closest_by_name(normalized_name)
                except ObjectDoesNotExist:
                    try:
                        TrophyService.get_closest_by_name(normalized_name)
                    except ObjectDoesNotExist:
                        filtered_items.append(item)

        tokens = list(Trophy.objects.values_list("tokens", flat=True))
        tokens.extend(list(Flag.objects.values_list("tokens", flat=True)))
        tokens = set(flatten(tokens))

        for item in filtered_items:
            name = normalize_race_name(item.name, is_female=is_female)
            name = normalize_synonyms(name, SYNONYMS)
            name = remove_symbols(remove_conjunctions(name))
            name = whitespaces_clean(name)
            names = normalize_name_parts(name)

            item_tokens = flatten([list(lemmatize(n)) for (n, _) in names])
            print(item.name)
            print("\t", names)
            print("\t", [i for i in item_tokens if i not in tokens])
