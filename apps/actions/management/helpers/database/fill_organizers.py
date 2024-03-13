import logging

import inquirer
from django.db.models.query import RawQuerySet

from apps.entities.models import Entity
from apps.races.models import Flag, Race, Trophy
from pyutils.strings import int_or_none

logger = logging.getLogger(__name__)


def fill_organizers(model: type[Trophy | Flag] | None, **_):
    if not model:
        fill_organizers(Trophy)
        fill_organizers(Flag)
        return

    model_name = model.__name__.lower()
    logger.info(f"processing {model_name}")
    query = f"""
        SELECT * FROM {model_name} m 
        WHERE EXISTS(SELECT * FROM race WHERE {model_name}_id = m.id AND organizer_id IS NULL)
            AND EXISTS(SELECT * FROM race WHERE {model_name}_id = m.id AND organizer_id IS NOT NULL)
    """
    items = model.objects.raw(query)
    _process(items, model_name)


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

        if existing.count() == 0:
            logger.info(f"no organizers found for {key}={item.name}")
            continue

        logger.info(f"found existing organizers for {key}={item.name}")
        choices = [(f"{e.pk} - {e}", e.pk) for e in existing]
        choices.append(("None", None))

        organizer_id = inquirer.list_input(
            message=f"{i+1}/{num_items} Select organizer_id for {key}=({item.pk} - {item})",
            choices=choices,
        )

        organizer_id = int_or_none(organizer_id)
        if organizer_id:
            Race.objects.filter(**{key: item}, organizer_id__isnull=True).update(organizer_id=organizer_id)
