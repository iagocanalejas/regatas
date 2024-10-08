# Generated by Django 5.0.8 on 2024-08-09 08:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("places", "0001_initial"),
        ("races", "0010_race_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="race",
            name="place",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="races",
                related_query_name="race",
                to="places.place",
            ),
        ),
    ]
