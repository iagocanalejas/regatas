# Generated by Django 5.0.4 on 2024-04-16 10:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("participants", "0002_participant_handicap"),
    ]

    operations = [
        migrations.AlterField(
            model_name="penalty",
            name="reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("NO_LINE_START", "Salida sin estacha"),
                    ("NULL_START", "Salida nula"),
                    ("COLLISION", "Colisión"),
                    ("BLADE_TOUCH", "Toque de palas"),
                    ("OFF_THE_FIELD", "Fuera de campo"),
                    ("COVID_ABSENCE", "Ausencia por COVID-19"),
                ],
                default=None,
                max_length=500,
                null=True,
            ),
        ),
    ]
