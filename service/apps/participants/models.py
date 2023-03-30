from django.contrib.postgres.fields import ArrayField
from django.db import models, IntegrityError

from ai_django.ai_core.models import CreationStampModel
from utils.choices import PENALTY_CHOICES, PARTICIPANT_CATEGORY_ABSOLUT, PARTICIPANT_CATEGORIES_CHOICES, ENTITY_CLUB, GENDER_MALE, \
    GENDER_CHOICES


class Participant(models.Model):
    club_name = models.CharField(null=True, blank=True, default=None, max_length=150)
    club = models.ForeignKey(
        null=False,
        to='entities.Entity',
        on_delete=models.CASCADE,
        related_name='participation',
        related_query_name='participation',
        limit_choices_to={'type': ENTITY_CLUB},
    )
    race = models.ForeignKey(
        null=False,
        to='races.Race',
        on_delete=models.CASCADE,
        related_name='participants',
        related_query_name='participant',
    )
    distance = models.PositiveIntegerField(null=True, blank=True, default=None)
    laps = ArrayField(blank=True, default=list, base_field=models.TimeField(null=False))
    lane = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    series = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    gender = models.CharField(default=GENDER_MALE, max_length=10, choices=GENDER_CHOICES)
    category = models.CharField(default=PARTICIPANT_CATEGORY_ABSOLUT, max_length=10, choices=PARTICIPANT_CATEGORIES_CHOICES)

    def __str__(self):
        title = f'{self.club.title.name}' if self.club.title else ''
        club = f'{title} {self.club_name}'.strip() if self.club_name else self.club
        return f'{self.race.date} :: {club} ({self.gender}) ({self.category}) -> {self.race.name}'

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
        to=Participant,
        on_delete=models.CASCADE,
        related_name='penalties',
        related_query_name='penalty',
    )

    def __str__(self):
        if self.disqualification:
            return f'Disqualified: {self.participant}'
        return f'Penalty ({self.reason}: {self.penalty}) -> {self.participant}'

    class Meta:
        db_table = 'penalty'
        verbose_name = 'Penalización'
        verbose_name_plural = 'Penalizaciones'
        ordering = ['participant']
