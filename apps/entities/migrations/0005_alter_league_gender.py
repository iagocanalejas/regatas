# Generated by Django 4.2.1 on 2023-06-13 11:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("entities", "0004_refactor_entities"),
    ]

    operations = [
        migrations.AlterField(
            model_name="league",
            name="gender",
            field=models.CharField(
                choices=[("MALE", "Male"), ("FEMALE", "Female"), ("MIX", "Mixto")],
                default=None,
                max_length=10,
                null=True,
            ),
        ),
    ]
