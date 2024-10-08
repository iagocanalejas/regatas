# Generated by Django 4.1.6 on 2023-02-12 17:50

import django.contrib.postgres.fields
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EntityTitle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True)),
                ("show_after", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Titulo",
                "db_table": "entity_tite",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="League",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_date", models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ("to_date", models.DateTimeField(blank=True, default=None, null=True)),
                ("is_active", models.BooleanField(blank=True, db_index=True, default=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                ("symbol", models.CharField(max_length=10)),
                (
                    "gender",
                    models.CharField(choices=[("MALE", "Male"), ("FEMALE", "Female"), ("MIX", "Mixto")], max_length=10),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        default=None, null=True, on_delete=models.deletion.PROTECT, to="entities.league"
                    ),
                ),
            ],
            options={
                "verbose_name": "Liga",
                "db_table": "league",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Entity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_date", models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
                ("to_date", models.DateTimeField(blank=True, default=None, null=True)),
                ("is_active", models.BooleanField(blank=True, db_index=True, default=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                ("official_name", models.CharField(max_length=150, unique=True)),
                (
                    "other_names",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=150), default=list, blank=True, size=None
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("CLUB", "Club"),
                            ("LEAGUE", "Liga"),
                            ("FEDERATION", "Federación"),
                            ("PRIVATE", "Privada"),
                        ],
                        max_length=50,
                    ),
                ),
                ("symbol", models.CharField(blank=True, default=None, max_length=10, null=True)),
                (
                    "title",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=models.deletion.PROTECT,
                        related_name="entities",
                        related_query_name="entity",
                        to="entities.entitytitle",
                    ),
                ),
            ],
            options={
                "verbose_name": "Entidad",
                "verbose_name_plural": "Entidades",
                "db_table": "entity",
                "ordering": ["type", "name"],
            },
        ),
    ]
