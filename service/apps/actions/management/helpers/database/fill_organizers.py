import logging

import inquirer
from django.db.models.query import RawQuerySet

from apps.entities.models import Entity
from apps.races.models import Flag, Race, Trophy

logger = logging.getLogger(__name__)


def fill_organizers(model: str = "all", **_):
    if model == "all" or model in ["trophy", "trophies"]:
        logger.info("Processing Trophies")
        query = """
            SELECT * FROM trophy t WHERE EXISTS(SELECT * FROM race WHERE trophy_id = t.id AND organizer_id IS NULL)
        """
        items = Trophy.objects.raw(query)
        _process(items, "trophy")

    if model == "all" or model in ["flag", "flags"]:
        logger.info("Processing Flags")
        query = """
            SELECT * FROM flag f WHERE EXISTS(SELECT * FROM race WHERE flag_id = f.id AND organizer_id IS NULL)
        """
        items = Flag.objects.raw(query)
        _process(items, "flag")


def _process(items: RawQuerySet, key: str):
    num_items = len(items)
    if num_items == 0:
        logger.info(f"No {key} to process")
        return
    for i, item in enumerate(items):
        existing = Entity.objects.filter(
            pk__in=(
                Race.objects.filter(**{key: item})
                .order_by("organizer_id")
                .distinct("organizer_id")
                .values_list("organizer_id", flat=True)
            )
        )

        if existing.count() > 0:
            logger.info(f"Found existing organizers for {key}={item.name}")
            for e in existing:
                logger.info(f"({e.pk}, {e.name})")

        organizer_id = inquirer.text(
            message=f"{i+1}/{num_items} Enter organizer_id for {key}=({item.pk}, {item.name})",
            default="",
        )
        organizer_id = _parse_int(organizer_id)
        if organizer_id:
            Race.objects.filter(**{key: item}, organizer_id__isnull=True).update(organizer_id=organizer_id)


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
