# Generated by Django 4.2.5 on 2023-10-03 14:43

import django.db.models.deletion
from django.db import migrations, models
from django.db.models.query_utils import Q


def update_associated(apps, _):
    Race = apps.get_model("races", "Race")

    for race in Race.objects.filter(day=2):
        match = Race.objects.get(
            Q(trophy_id=race.trophy_id) | Q(trophy_id__isnull=True),
            Q(trophy_edition=race.trophy_edition) | Q(trophy_edition__isnull=True),
            flag_id=race.flag_id,
            flag_edition=race.flag_edition,
            league_id=race.league_id,
            date__year=race.date.year,
            day=1,
        )

        match.associated_id = race.pk
        race.associated_id = match.pk

        print(f"{match.pk} linked to {race.pk}")
        match.save()
        race.save()


class Migration(migrations.Migration):
    dependencies = [
        ("races", "0005_flag_qualifies_for_trophy_qualifies_for"),
    ]

    operations = [
        migrations.AddField(
            model_name="race",
            name="associated",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="races.race",
            ),
        ),
        migrations.RunPython(update_associated, reverse_code=migrations.RunPython.noop),
    ]
