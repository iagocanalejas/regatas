# Generated by Django 4.2.1 on 2023-06-03 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0002_entity_metadata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entity',
            name='title',
        ),
        migrations.AlterField(
            model_name='entity',
            name='name',
            field=models.CharField(max_length=150),
        ),
        migrations.DeleteModel(
            name='EntityTitle',
        ),
    ]