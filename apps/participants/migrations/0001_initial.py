# Generated by Django 4.1.6 on 2023-02-12 17:50

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("races", "0001_initial"),
        ("entities", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Participant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("club_name", models.CharField(blank=True, default=None, max_length=150, null=True)),
                ("distance", models.PositiveIntegerField(blank=True, default=None, null=True)),
                (
                    "laps",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TimeField(), blank=True, default=list, size=None
                    ),
                ),
                ("lane", models.PositiveSmallIntegerField(blank=True, default=None, null=True)),
                ("series", models.PositiveSmallIntegerField(blank=True, default=None, null=True)),
                (
                    "gender",
                    models.CharField(
                        choices=[("MALE", "Male"), ("FEMALE", "Female"), ("MIX", "Mixto")],
                        default="MALE",
                        max_length=10,
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[("ABSOLUT", "Absoluto"), ("VETERAN", "Veterano"), ("SCHOOL", "Escuela")],
                        default="ABSOLUT",
                        max_length=10,
                    ),
                ),
                (
                    "club",
                    models.ForeignKey(
                        limit_choices_to={"type": "CLUB"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participation",
                        related_query_name="participation",
                        to="entities.entity",
                    ),
                ),
                (
                    "race",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        related_query_name="participant",
                        to="races.race",
                    ),
                ),
            ],
            options={
                "verbose_name": "Participante",
                "verbose_name_plural": "Participantes",
                "db_table": "participant",
                "ordering": ["race", "club"],
            },
        ),
        migrations.CreateModel(
            name="Penalty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("penalty", models.PositiveIntegerField(blank=True, default=0)),
                ("disqualification", models.BooleanField(default=False)),
                (
                    "reason",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("NO_LINE_START", "Salida sin estacha"),
                            ("NULL_START", "Salida nula"),
                            ("BLADE_TOUCH", "Toque de palas"),
                        ],
                        default=None,
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="penalties",
                        related_query_name="penalty",
                        to="participants.participant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Penalización",
                "verbose_name_plural": "Penalizaciones",
                "db_table": "penalty",
                "ordering": ["participant"],
            },
        ),
    ]
