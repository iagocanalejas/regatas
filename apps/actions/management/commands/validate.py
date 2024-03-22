#!/usr/bin/env python3

import logging

from django.core.management import BaseCommand

from apps.actions.management.ingestor import IngestorProtocol, build_ingestor
from apps.participants.models import Participant
from apps.races.services import MetadataService
from rscraping.clients import TabularClientConfig
from rscraping.data.constants import GENDER_FEMALE
from rscraping.data.models import Datasource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Retrieve races from the database and verifies it's datasources ara correct.

    Usage:
    python manage.py validatedatasource datasource [year]

    Arguments:
        datasource:
            The name of the Datasource that will be validated.

        year:
            The year of the races that will be processed.
    """

    _cached_ingestor: dict[str, IngestorProtocol] = {}

    def add_arguments(self, parser):
        parser.add_argument("datasource", type=str, help="The name of the Datasource that will be validated")
        parser.add_argument(
            "year",
            nargs="?",
            type=int,
            default=None,
            help="The year for which race data should be verified.",
        )

    def handle(self, *_, **options):
        logger.info(f"{options}")

        maybe_datasource, year = options["datasource"], options["year"]
        if maybe_datasource and not Datasource.has_value(maybe_datasource):
            raise ValueError(f"invalid datasource={maybe_datasource}")
        datasource = Datasource(maybe_datasource)

        races = MetadataService.get_races_by_datasource(datasource)
        if year:
            races = races.filter(date__year=year)

        for race in races:
            logger.info(f"processing {race=}")
            sources = race.metadata.get("datasource", [])
            sources = [d for d in sources if datasource is None or d.get("datasource_name") == datasource.value.lower()]
            for d in sources:
                ref_id = d.get("ref_id", None)
                url = d.get("values", {}).get("details_page", None)
                if not url or not ref_id:
                    logger.error(f"no {ref_id=} or {url=} found for a datasource in {race=}")
                    # this should never happen
                    input("Press Enter to continue...")
                    continue

                ingestor = self._get_ingestor(datasource, url, race.gender == GENDER_FEMALE)
                scrapped_race = ingestor.fetch_by_url(url, race_id=ref_id)

                # this block should also never happen
                if not scrapped_race:
                    logger.error(f"no race found for {race=}")
                    input("Press Enter to continue...")
                    continue
                if len(scrapped_race.race_ids) != 1:
                    logger.error(f"more than one race found for {race=}")
                    continue

                race, verified, needs_update = ingestor.verify(race, scrapped_race)
                if verified:
                    if needs_update:
                        logger.info(f"updating {race=}")
                        ingestor.save(race)

                    if datasource == Datasource.LGT:
                        logger.error(
                            "We can't verify LGT participants because the are !!!FUCKING DUMB!!! "
                            + "and replace the names of the participants each year."
                        )
                        continue

                    participants = list(Participant.objects.filter(race=race))
                    participants = ingestor.verify_participants(race, participants, scrapped_race.participants)
                    for p, verified, needs_update in participants:
                        if verified and needs_update:
                            logger.info(f"updating {p=}")
                            ingestor.save_participant(p)

    def _get_ingestor(self, datasource: Datasource, url: str, is_female: bool):
        if datasource == Datasource.TABULAR and url in self._cached_ingestor:
            return self._cached_ingestor[url]

        config = TabularClientConfig(sheet_url=url)
        ingestor = build_ingestor(datasource, config, is_female, None, [])
        if datasource == Datasource.TABULAR:
            self._cached_ingestor[url] = ingestor
        return ingestor
