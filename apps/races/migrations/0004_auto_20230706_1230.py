# Generated by Django 4.2.1 on 2023-07-06 12:30

from django.db import migrations
from django.db.models import Q

from apps.utils.choices import GENDER_FEMALE, GENDER_MALE
from rscraping.data.models import Datasource


def update_metadata(apps, _):
    Race = apps.get_model("races", "Race")
    races = Race.objects.filter(
        Q(metadata__datasource__contains=[{"datasource_name": Datasource.ACT.value}])
        | Q(metadata__datasource__contains=[{"datasource_name": Datasource.ARC.value}])
    )
    for race in races:
        datasource = race.metadata["datasource"][0]
        if values := datasource["values"]:
            print(f"updating metadata: {datasource}")
            url = values["details_page"]
            is_female = any(e in url for e in ["ligaete", "/femenina/"])

            datasource["values"]["gender"] = GENDER_FEMALE if is_female else GENDER_MALE
            print(datasource)
            race.metadata["datasource"][0] = datasource

    Race.objects.bulk_update(races, ["metadata"])


class Migration(migrations.Migration):
    dependencies = [
        ("races", "0003_alter_race_metadata"),
    ]

    operations = [
        migrations.RunPython(update_metadata, reverse_code=migrations.RunPython.noop),
    ]
