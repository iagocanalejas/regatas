# Generated by Django 5.0.8 on 2024-08-23 11:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('races', '0011_race_place'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='race',
            name='town',
        ),
    ]
