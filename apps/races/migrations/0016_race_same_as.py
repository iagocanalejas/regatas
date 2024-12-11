# Generated by Django 5.1.1 on 2024-11-18 10:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("races", "0015_alter_race_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="race",
            name="same_as",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="races.race",
            ),
        ),
    ]