# Generated by Django 5.1.6 on 2025-02-23 15:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("races", "0016_race_same_as"),
    ]

    operations = [
        migrations.AddField(
            model_name="flag",
            name="last_checked",
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
