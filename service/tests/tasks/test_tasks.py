import os

import responses
from django.conf import settings
from django.test import TestCase

from apps.actions.datasource import Datasource
from apps.actions.models import Task, STATUS_PENDING
from apps.actions.tasks import get_new_races, process_tasks
from tests.utils import add_html_response
from utils.choices import GENDER_MALE


class NewRacesTest(TestCase):
    @responses.activate
    def test_get_new_races(self):
        add_html_response("https://www.euskolabelliga.com/resultados/index.php?t=2023", 'euskolabelliga.html')
        add_html_response("https://www.euskolabelliga.com/femenina/resultados/index.php?t=2023", 'euskolabelliga.html')
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt.html', method=responses.POST)
        add_html_response("https://www.liga-arc.com/es/resultados/2023", 'arc_v2.html')
        add_html_response("https://www.ligaete.com/es/resultados/2023", 'arc_v2.html')

        # empty results to halt the LGT processing
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)
        add_html_response('https://www.ligalgt.com/ajax/principal/ver_resultados.php', 'lgt_empty.html', method=responses.POST)

        get_new_races()

        self.assertTrue(Task.objects.filter(race_id='1647864858').exists())
        self.assertTrue(Task.objects.filter(race_id='2').exists())
        self.assertTrue(Task.objects.filter(race_id='29').exists())


class ProcessNewRacesTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    # noinspection LongLine
    @responses.activate
    def test_process_tasks(self):
        task = Task(race_id='1647864858', gender=GENDER_MALE, datasource=Datasource.ACT, status=STATUS_PENDING)
        task.save()

        add_html_response("https://www.euskolabelliga.com/resultados/ver.php?r=1647864858", 'euskolabelliga_details.html')

        process_tasks()
        task.refresh_from_db()

        self.assertEqual(
            task.details, {
                'race': {
                    'day': 1,
                    'date': '2022-07-17',
                    'laps': 4,
                    'town': 'ZIERBENA BIZKAIA',
                    'type': 'CONVENTIONAL',
                    'lanes': 4,
                    'flag_id': 85,
                    'metadata': {
                        'datasource': [
                            {
                                'values': {
                                    'details_page': 'https://www.euskolabelliga.com/resultados/ver.php?r=1647864858'
                                },
                                'ref_id': '1647864858',
                                'datasource_name': 'act'
                            }
                        ]
                    },
                    'modality': 'TRAINERA',
                    'league_id': 2,
                    'race_name': 'BANDERA PETRONOR',
                    'flag_edition': 39
                },
                'participants': [
                    {
                        'lane': 3,
                        'laps': ['00:05:03', '00:09:57', '00:15:20', '00:20:09.900000'],
                        'gender': 'MALE',
                        'series': 1,
                        'club_id': 37,
                        'category': 'ABSOLUT',
                        'distance': 5556,
                        'club_name': 'GETARIA'
                    }, {
                        'lane': 4,
                        'laps': ['00:05:05', '00:09:59', '00:15:26', '00:20:20.980000'],
                        'gender': 'MALE',
                        'series': 2,
                        'club_id': 45,
                        'category': 'ABSOLUT',
                        'distance': 5556,
                        'club_name': 'ZIERBENA BAHIAS DE BIZKAIA'
                    }, {
                        'lane': 2,
                        'laps': ['00:04:57', '00:09:44', '00:15:05', '00:19:54.520000'],
                        'gender': 'MALE',
                        'series': 3,
                        'club_id': 42,
                        'category': 'ABSOLUT',
                        'distance': 5556,
                        'club_name': 'MATRIX HONDARRIBIA'
                    }
                ]
            }
        )
