# Generated by Django 4.1.7 on 2023-03-31 11:34

import djutils.validators.schema
from django.db import migrations, models

import apps.schemas


class Migration(migrations.Migration):
    dependencies = [
        ("entities", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="entity",
            name="metadata",
            field=models.JSONField(
                default=apps.schemas.default_metadata,
                validators=[
                    djutils.validators.schema.JSONSchemaValidator(
                        schema={
                            "$schema": "http://json-schema.org/schema#",
                            "name": "RaceMetadata",
                            "properties": {
                                "datasource": {
                                    "items": {
                                        "additionalProperties": False,
                                        "properties": {
                                            "datasource_name": {"type": "string"},
                                            "ref_id": {"type": "string"},
                                            "values": {"additionalProperties": {"type": "string"}, "type": "object"},
                                        },
                                        "required": ["datasource_name", "values"],
                                        "type": "object",
                                    },
                                    "type": "array",
                                }
                            },
                            "required": ["datasource"],
                        }
                    )
                ],
            ),
        ),
    ]
