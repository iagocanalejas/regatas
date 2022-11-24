import os
from ast import literal_eval

import yaml
from django.core.management import BaseCommand
from yaml import SafeLoader

from apps.participants.models import Participant
from apps.races.models import Flag, Trophy, Race


class Command(BaseCommand):
    help = 'Import yaml from the old schema (race only have the "trophy" relation) to the new trophy/flag schema.'

    _trophies_map = {}
    _flags_map = {}
    _races_map = {}

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)

    def handle(self, *args, **options):
        assert options['path']

        for file in options['path']:
            assert os.path.isfile(file)

            with open(file) as f:
                for obj in yaml.load(f, Loader=SafeLoader):
                    print(obj)
                    fields = obj['fields']
                    if obj['model'] == 'races.trophy':
                        if 'GRAN' in fields['name'] or 'PLAY' in fields['name']:
                            trophy = Trophy(name=fields['name'])
                            trophy.save()

                            self._trophies_map[obj['pk']] = trophy.pk
                            continue
                        else:
                            try:
                                flag = Flag.objects.get(name=fields['name'])
                            except Flag.DoesNotExist:
                                flag = Flag(name=fields['name'])
                                flag.save()

                            self._flags_map[obj['pk']] = flag.pk
                            continue
                    # if obj['model'] == 'races.extratrophy':
                    #     try:
                    #         flag = Flag.objects.get(name=fields['name'])
                    #     except Flag.DoesNotExist:
                    #         flag = Flag(name=fields['name'])
                    #         flag.save()
                    #
                    #     self.flags_map[obj['pk']] = flag.pk
                    #     continue
                    if obj['model'] == 'races.race':
                        trophy = flag = None
                        trophy_edition = flag_edition = None

                        try:
                            trophy = self._trophies_map[fields['trophy']]
                            trophy_edition = fields['edition']
                        except KeyError:
                            flag = self._flags_map[fields['trophy']]
                            flag_edition = fields['edition']

                        race = Race(
                            laps=fields['laps'],
                            lanes=fields['lanes'],
                            town=fields['town'],
                            type=fields['type'],
                            date=fields['date'],
                            day=fields['day'],
                            race_name=fields['race_name'],
                            league_id=fields['league'],
                            organizer_id=fields['organizer'],
                            metadata=fields['metadata'],
                            trophy_id=trophy,
                            trophy_edition=trophy_edition,
                            flag_id=flag,
                            flag_edition=flag_edition
                        )
                        race.save()

                        self._races_map[obj['pk']] = race.pk
                        continue
                    if obj['model'] == 'participants.participant':
                        participants = Participant(
                            club_id=fields['club'],
                            club_name=fields['club_name'],
                            race_id=self._races_map[fields['race']],
                            distance=fields['distance'],
                            laps=literal_eval(fields['laps']),
                            lane=fields['lane'],
                            series=fields['series'],
                        )
                        participants.save()
                        continue
