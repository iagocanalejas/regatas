# Generated by Django 5.0.6 on 2024-06-13 09:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("entities", "0008_alter_entity_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="category",
            field=models.CharField(
                choices=[("SCHOOL", "School"), ("ABSOLUT", "Absolut"), ("VETERAN", "Veteran")],
                default=None,
                max_length=10,
                null=True,
            ),
        ),
    ]