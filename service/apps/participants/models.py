from django.contrib.postgres.fields import ArrayField
from django.db import models, IntegrityError

from ai_django.ai_core.models import CreationStampModel
from apps.entities.models import ENTITY_CLUB

NO_LINE_START = 'NO_LINE_START'
NULL_START = 'NULL_START'
BLADE_TOUCH = 'BLADE_TOUCH'

PENALTY_CHOICES = [
    (NO_LINE_START, 'Salida sin estacha'),
    (NULL_START, 'Salida nula'),
    (BLADE_TOUCH, 'Toque de palas'),
]


class Participant(models.Model):
    club_name = models.CharField(null=True, blank=True, default=None, max_length=150)
    club = models.ForeignKey(
        null=False,
        to='entities.Entity', on_delete=models.CASCADE,
        related_name='participation', related_query_name='participation',
        limit_choices_to={'type': ENTITY_CLUB},
    )
    race = models.ForeignKey(
        null=False,
        to='races.Race', on_delete=models.CASCADE,
        related_name='participants', related_query_name='participant',
    )
    distance = models.PositiveIntegerField(null=True, blank=True, default=None)
    laps = ArrayField(blank=True, default=list, base_field=models.TimeField(null=False))
    lane = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    series = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    def __str__(self):
        title = f'{self.club.title.name}' if self.club.title else ''
        club = f'{title} {self.club_name}'.strip() if self.club_name else self.club
        return f'{self.race.date} :: {club} -> {self.race.name}'

    @property
    def time(self):
        return self.laps[-1]

    def validate_unique(self, exclude=None):
        """
        Validate a club can't participate twice in a race unless it's in different leagues.
        """
        if self.race_id and self.race.league_id:
            query = self.__class__.objects.filter(
                race__league__isnull=False,
                race__league_id=self.race.league_id,
                club_id=self.club_id,
                race_id=self.race_id,
            )
            if query.exists():
                raise IntegrityError(
                    f'Instance with club:{self.club_id}, race:{self.race_id} and '
                    f'league:{self.race.league_id} already exists.',
                )

    def save(self, *args, **kwargs):
        if self.pk is None:  # TODO: implement update validation
            self.validate_unique()

        super(Participant, self).save(*args, **kwargs)

    class Meta:
        db_table = 'participant'
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        ordering = ['race', 'club']


class Penalty(models.Model):
    penalty = models.PositiveIntegerField(blank=True, default=0)
    disqualification = models.BooleanField(default=False)
    reason = models.CharField(null=True, blank=True, default=None, max_length=500, choices=PENALTY_CHOICES)  # TODO: convert to NON-NULLABLE
    participant = models.ForeignKey(
        null=False,
        to=Participant, on_delete=models.CASCADE,
        related_name='penalties', related_query_name='penalty',
    )

    class Meta:
        db_table = 'penalty'
        verbose_name = 'Penalización'
        verbose_name_plural = 'Penalizaciones'
        ordering = ['participant']
