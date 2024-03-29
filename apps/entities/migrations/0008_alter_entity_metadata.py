# Generated by Django 5.0.3 on 2024-03-19 20:23

from django.db import migrations, models

import apps.schemas
import djutils.validators.schema


class Migration(migrations.Migration):
    dependencies = [
        ("entities", "0007_alter_entitypartnership_target"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entity",
            name="metadata",
            field=models.JSONField(
                default=apps.schemas.default_metadata,
                validators=[
                    djutils.validators.schema.JSONSchemaValidator(
                        schema={
                            "$schema": "http://json-schema.org/schema#",
                            "name": "EntityMetadata",
                            "properties": {
                                "datasource": {
                                    "items": {
                                        "additionalProperties": False,
                                        "properties": {
                                            "datasource_name": {"type": "string"},
                                            "ref_id": {"type": "string"},
                                            "values": {"additionalProperties": {"type": "string"}, "type": "object"},
                                        },
                                        "required": ["ref_id", "datasource_name", "values"],
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
