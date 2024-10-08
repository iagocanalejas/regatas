# Generated by Django 5.0.8 on 2024-08-09 08:34

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Town",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("province", models.CharField(max_length=100)),
                (
                    "known_names",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=150), blank=True, default=list, size=None
                    ),
                ),
            ],
            options={
                "verbose_name": "Municipio",
                "verbose_name_plural": "Municipios",
                "db_table": "town",
                "ordering": ["name"],
                "unique_together": {("name", "province")},
            },
        ),
        migrations.CreateModel(
            name="Place",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                (
                    "known_names",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=150), blank=True, default=list, size=None
                    ),
                ),
                (
                    "town",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="places",
                        related_query_name="place",
                        to="places.town",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lugar",
                "verbose_name_plural": "Lugares",
                "db_table": "place",
                "ordering": ["name"],
                "unique_together": {("name", "town")},
            },
        ),
    ]
