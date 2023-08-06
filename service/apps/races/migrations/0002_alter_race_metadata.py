# Generated by Django 4.1.7 on 2023-03-01 10:21

from django.db import migrations, models

import ai_django.ai_core.validators.schema
import apps.schemas
from rscraping import Datasource


def update_metadata(apps, schema_editor):
    Race = apps.get_model('races', 'Race')
    races = Race.objects.filter(metadata__datasource__contains=[{"values": []}])
    for race in races:
        print(f"updating metadata: {race.metadata['datasource'][0]}")
        datasource = race.metadata['datasource'][0]
        if datasource['datasource_name'] == Datasource.INFOREMO.value:
            # for 'inforemo' save only the datasource name as no more useful information can be retrieved
            datasource = {'datasource_name': Datasource.INFOREMO.value, 'values': {}}
        else:
            # for all the scrappers update the 'race_id' and 'values'
            datasource['race_id'] = str(datasource['race_id'])
            datasource['values'] = datasource['values'][0] if len(datasource['values'][0]) > 0 else {}
        print(datasource)
        race.metadata['datasource'][0] = datasource

    Race.objects.bulk_update(races, ['metadata'])


class Migration(migrations.Migration):
    dependencies = [
        ('races', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='race',
            name='metadata',
            field=models.JSONField(
                default=apps.schemas.default_metadata,
                validators=[
                    ai_django.ai_core.validators.schema.JSONSchemaValidator(
                        schema={
                            '$schema': 'http://json-schema.org/schema#',
                            'name': 'RaceMetadata',
                            'properties': {
                                'datasource': {
                                    'items': {
                                        'additionalProperties': False,
                                        'properties': {
                                            'datasource_name': {
                                                'type': 'string'
                                            },
                                            'race_id': {
                                                'type': 'string'
                                            },
                                            'values': {
                                                'additionalProperties': {
                                                    'type': 'string'
                                                },
                                                'type': 'object'
                                            }
                                        },
                                        'required': ['datasource_name', 'values'],
                                        'type': 'object'
                                    },
                                    'type': 'array'
                                }
                            },
                            'required': ['datasource']
                        }
                    )
                ]
            ),
        ),
        migrations.RunPython(update_metadata, reverse_code=migrations.RunPython.noop),
    ]
