# Generated by Django 5.0.6 on 2024-06-18 09:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("participants", "0006_participant_absent_participant_guest"),
    ]

    operations = [
        migrations.AddField(
            model_name="participant",
            name="retired",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="penalty",
            name="reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("BOAT_WEIGHT_LIMIT", "Fuera de peso"),
                    ("COLLISION", "Colisión"),
                    ("COXWAIN_WEIGHT_LIMIT", "Timonel fuera de peso"),
                    ("LACK_OF_COMPETITIVENESS", "Falta de competitividad"),
                    ("NO_LINE_START", "Salida sin estacha"),
                    ("NULL_START", "Salida nula"),
                    ("OFF_THE_FIELD", "Fuera de campo"),
                    ("SINKING", "Hundimiento"),
                    ("STARBOARD_TACK", "Virada por estribor"),
                    ("WRONG_LINEUP", "Alineación incorrecta"),
                    ("WRONG_ROUTE", "Ruta/Llegada incorrecta"),
                ],
                default=None,
                max_length=500,
                null=True,
            ),
        ),
    ]
