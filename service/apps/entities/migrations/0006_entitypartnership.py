# Generated by Django 4.2.1 on 2023-07-05 13:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('entities', '0005_alter_league_gender'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityPartnership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(blank=True, db_index=True, default=True)),
                ('part', models.ForeignKey(limit_choices_to={False, 'is_partnership'}, on_delete=django.db.models.deletion.PROTECT,
                                           related_name='part_of', related_query_name='part_of', to='entities.entity')),
                ('target', models.ForeignKey(limit_choices_to={True, 'is_partnership'}, on_delete=django.db.models.deletion.PROTECT,
                                             related_name='components', related_query_name='component', to='entities.entity')),
            ],
            options={
                'verbose_name': 'Fusión',
                'verbose_name_plural': 'Fusiones',
                'db_table': 'entity_partnership',
            },
        ),
    ]
