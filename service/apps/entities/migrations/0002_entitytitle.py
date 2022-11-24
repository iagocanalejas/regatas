# Generated by Django 4.1.1 on 2022-09-17 10:22

import django.db.models.deletion
from django.db import migrations, models


# noinspection LongLine
def insert_entity_titles(apps, schema_editor):
    EntityTitle = apps.get_model('entities', 'EntityTitle')

    EntityTitle(name='CLUB REMO').save()
    EntityTitle(name='CLUB DE REMO').save()
    EntityTitle(name='SOCIEDAD DEPORTIVA').save()
    EntityTitle(name='SOCIEDAD DEPORTIVA DE REMO').save()
    EntityTitle(name='CLUB DO MAR').save()
    EntityTitle(name='CLUB DE REGATAS').save()
    EntityTitle(name='ASOCIACION DEPORTIVA').save()
    EntityTitle(name='CIRCULO CULTURAL').save()


class Migration(migrations.Migration):
    dependencies = [
        ('entities', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
            ],
            options={
                'verbose_name': 'Titulo',
                'db_table': 'entity_tite',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='entity',
            name='title',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='entities', related_query_name='entity', to='entities.entitytitle'),
        ),
        migrations.AlterModelOptions(
            name='entity',
            options={'ordering': ['type', 'title', 'name'], 'verbose_name': 'Entidad'},
        ),
        migrations.RunPython(insert_entity_titles),
    ]
