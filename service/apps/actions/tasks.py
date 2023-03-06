import datetime
import itertools
import logging
from typing import List

from django.utils import timezone

from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.actions.models import Task, STATUS_PENDING, STATUS_PROCESSED
from apps.races.models import Race
from apps.races.services import RaceService
from config.celery import app
from utils.choices import GENDER_FEMALE, GENDER_MALE

logger = logging.getLogger(__name__)


def _should_create_task(race_id: str, datasource: str, tasks: List[Task]) -> bool:
    exists_in_db = RaceService.get_filtered(
        queryset=Race.objects, filters={'metadata': [{
            "race_id": race_id,
            "datasource_name": datasource
        }]}
    )
    exists_in_tasks = any(t.race_id == race_id for t in tasks)
    return not exists_in_db and not exists_in_tasks


def _resolve_date(value):
    if isinstance(value, datetime.date) or isinstance(value, datetime.time):
        return value.isoformat()
    if isinstance(value, list):
        return [_resolve_date(e) for e in value]
    return value


@app.task
def get_new_races():
    logger.info('running task "get_new_races"')
    season = datetime.date.today().year
    datasources = [Datasource.ACT, Datasource.LGT, Datasource.ARC]
    tasks = []

    for (datasource, is_female) in itertools.product(datasources, [True, False]):
        logger.info(f'get_new_races:: processing {datasource=}')
        client = Client(source=datasource)
        race_ids = client.get_ids_by_season(season=season, is_female=is_female)

        # filter already existing race_ids
        race_ids = filter(lambda race_id: _should_create_task(race_id, datasource.lower(), tasks), race_ids)

        # create datasource tasks
        new_tasks = [
            Task(
                datasource=datasource.lower(),
                gender=GENDER_FEMALE if is_female else GENDER_MALE,
                race_id=race_id,
                status=STATUS_PENDING,
                creation_date=timezone.now(),
            ) for race_id in race_ids
        ]
        logger.info(f'creating new task={new_tasks}')
        tasks.extend(new_tasks)

    # save new tasks
    logger.info(f'saving newly created {tasks=}')
    Task.objects.bulk_create(tasks)
    logger.info('finish task "get_new_races"')


@app.task
def process_tasks():
    logger.info('running task "process_tasks"')
    _clients = {}
    for task in Task.objects.filter(status=STATUS_PENDING):
        # for each pending Task retrieve the race details and save
        if task.datasource not in _clients:
            _clients[task.datasource] = Client(source=task.datasource)
        client = _clients[task.datasource]

        logger.info(f'process_tasks:: processing {task=}')
        race, participants = client.get_web_race_by_id(task.race_id, is_female=task.gender == GENDER_FEMALE)

        task.details = {
            'race': {
                k: _resolve_date(v)
                for k, v in race.__dict__.items()
                if not k.startswith('_') and k not in ['id', 'creation_date'] and v
            },
            'participants': [
                {k: _resolve_date(v)
                 for k, v in participant.__dict__.items()
                 if not k.startswith('_') and k not in ['id'] and v}
                for participant in participants
            ]
        }
        task.status = STATUS_PROCESSED
        task.processed_date = timezone.now()

        logger.info(f'process_tasks:: updated {task=}')
        task.save()
    logger.info('finish task "process_tasks"')
