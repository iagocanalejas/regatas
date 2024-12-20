from typing import Any

import inquirer

from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.races.models import Flag, Race, Trophy
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace


def input_new_value(key: str, value: Any, db_value: Any) -> bool:
    if not value or db_value == value:
        return False
    text = f"current {key} value is {db_value}, provided one is {value}"
    return inquirer.confirm(f"{text}. Do you want to UPDATE it?", default=False)


def input_should_merge(db_race: Race) -> bool:
    return inquirer.confirm(f"found matching race {db_race} in the database. Merge both races?")


def input_should_reset_league() -> bool:
    return inquirer.confirm("Should the league be reseted?")


def input_should_merge_participant(db_participant: Participant) -> bool:
    return inquirer.confirm(
        f"found matching participant {db_participant} in the database. Merge both participants?", default=False
    )


def input_should_add_datasource(db_participant: Participant) -> bool:
    return inquirer.confirm(f"Add new datasource for {db_participant}?", default=False)


def input_shoud_create_participant(participant: RSParticipant) -> bool:
    return inquirer.confirm(f"create new participation for {participant=}?", default=False)


def input_shoud_create_B_participant(participant: Participant) -> bool:
    return inquirer.confirm(f"create B team participation for {participant=}?", default=False)


def input_should_save(race: Race) -> bool:
    text = f"UPDATE existing {race=}?" if race.pk else f"SAVE new {race=}?"
    return inquirer.confirm(text, default=False)


def input_should_save_participant(participant: Participant) -> bool:
    text = f"UPDATE existing {participant=}?" if participant.pk else f"SAVE new {participant=}?"
    return inquirer.confirm(text, default=False)


def input_should_associate_races(race: Race, associated: Race) -> bool:
    return inquirer.confirm(f"link new race {race} with associated {associated}")


def input_should_save_second_day(race: Race):
    return inquirer.confirm(f"race {race} already in DB. Is this race a second day?")


def input_race(race: RSRace) -> Race | None:
    race_id = inquirer.text(f"no race found for {race.date}::{race.name}. Race ID", default=None)
    return Race.objects.get(id=race_id) if race_id else None


def input_associated(race: Race) -> Race | None:
    race_id = inquirer.text(f"no associated race found for {race.date}::{race.name}. Race ID", default=None)
    return Race.objects.get(id=race_id) if race_id else None


def input_competition(
    race: RSRace,
) -> tuple[Race | None, tuple[Trophy | None, int | None], tuple[Flag | None, int | None]]:
    db_race = input_race(race)
    if db_race:
        trophy, trophy_edition = db_race.trophy, db_race.trophy_edition
        flag, flag_edition = db_race.flag, db_race.flag_edition
        return db_race, (trophy, trophy_edition), (flag, flag_edition)
    return None, _input_competition(Trophy, race.name), _input_competition(Flag, race.name)


def _input_competition[T: Trophy | Flag](_model: type[T], name: str) -> tuple[T | None, int | None]:
    value = value_edition = None
    value_id = inquirer.text(f"no {_model.__name__.lower()} found for {name}. {_model.__name__} ID", default=None)
    if value_id:
        value = _model.objects.get(id=value_id)
        value_edition = int(inquirer.text(f"new edition for {_model.__name__}:{value}", default=None))
    return value, value_edition


def input_club(name: str) -> Entity | None:
    entity_id = inquirer.text(f"no entity found for {name}. Entity ID", default=None)
    if entity_id:
        return Entity.all_objects.get(id=entity_id)
    return None


def input_edition(model: Trophy | Flag, league: str | None) -> str | None:
    return inquirer.text(f"no edition found for {model.__class__.__name__.lower()} - {league}:{model}", default=None)
