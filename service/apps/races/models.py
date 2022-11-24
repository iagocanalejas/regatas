from django.contrib.postgres.fields import ArrayField
from django.db import models, IntegrityError
from django.db.models import JSONField

from ai_django.ai_core.models import CreationStampModel
from ai_django.ai_core.utils.shortcuts import all_or_none
from ai_django.ai_core.utils.strings import int_to_roman, whitespaces_clean
from ai_django.ai_core.validators import JSONSchemaValidator
from apps.entities.models import LEAGUE_GENDER_FEMALE, LEAGUE_GENDER_CHOICES
from apps.races.schemas import RACE_METADATA_SCHEMA, default_race_metadata
from utils.synonyms import lemmatize

RACE_CONVENTIONAL = 'CONVENTIONAL'
RACE_TIME_TRIAL = 'TIME_TRIAL'

RACE_TYPES = [RACE_CONVENTIONAL, RACE_TIME_TRIAL]
RACE_TYPE_CHOICES = [
    (RACE_CONVENTIONAL, 'Convencional'),
    (RACE_TIME_TRIAL, 'Contrarreloj'),
]

RACE_TRAINERA = 'TRAINERA'
RACE_VETERANS = 'VETERAN'
RACE_TRAINERILLA = 'TRAINERILLA'
RACE_BATEL = 'BATE'

RACE_MODALITIES = [RACE_TRAINERA, RACE_VETERANS, RACE_TRAINERILLA, RACE_BATEL]
RACE_MODALITY_CHOICES = [
    (RACE_TRAINERA, 'Trainera'),
    (RACE_VETERANS, 'Veteranos'),
    (RACE_TRAINERILLA, 'Trainerilla'),
    (RACE_BATEL, 'Batel'),
]


class Trophy(CreationStampModel):
    name = models.CharField(max_length=150, unique=True)
    tokens = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=50), editable=False)
    verified = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tokens = lemmatize(self.name)
        super(Trophy, self).save(*args, **kwargs)

    class Meta:
        db_table = 'trophy'
        verbose_name = 'Trofeo'
        verbose_name_plural = 'Trofeos'
        ordering = ['name']


class Flag(CreationStampModel):
    name = models.CharField(max_length=150, unique=True)
    tokens = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=50), editable=False)
    verified = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tokens = lemmatize(self.name)
        super(Flag, self).save(*args, **kwargs)

    class Meta:
        db_table = 'flag'
        verbose_name = 'Bandera'
        verbose_name_plural = 'Banderas'
        ordering = ['name']


# TODO: enum of cancellation reasons
class Race(CreationStampModel):
    laps = models.PositiveSmallIntegerField(null=True, blank=True, default=None)  # TODO: convert to NON-NULLABLE
    lanes = models.PositiveSmallIntegerField(null=True, blank=True, default=None)  # TODO: convert to NON-NULLABLE
    town = models.CharField(max_length=100, null=True, blank=True, default=None)

    type = models.CharField(max_length=50, choices=RACE_TYPE_CHOICES, default=RACE_CONVENTIONAL)
    date = models.DateField()
    day = models.PositiveSmallIntegerField(default=1)

    cancelled = models.BooleanField(default=False)
    cancellation_reasons = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=200))

    race_name = models.CharField(null=True, blank=True, default=None, max_length=200)
    sponsor = models.CharField(null=True, blank=True, default=None, max_length=200)

    # 'trophy_edition' and 'trophy' should both be NULL or NOT_NULL
    trophy_edition = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    trophy = models.ForeignKey(
        null=True, blank=True, default=None,
        to=Trophy, on_delete=models.PROTECT,
        related_name='editions', related_query_name='edition',
    )
    # 'flag_edition' and 'flag' should both be NULL or NOT_NULL
    flag_edition = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    flag = models.ForeignKey(
        null=True, blank=True, default=None,
        to=Flag, on_delete=models.PROTECT,
        related_name='editions', related_query_name='edition',
    )

    # only one of 'gender', 'league' should be NOT_NULL, both can be NULL at the same time
    gender = models.CharField(null=True, blank=True, default=None, max_length=10, choices=LEAGUE_GENDER_CHOICES)
    league = models.ForeignKey(
        null=True, blank=True, default=None,
        to='entities.League', on_delete=models.PROTECT,
        related_name='races', related_query_name='race',
    )

    modality = models.CharField(default=RACE_TRAINERA, max_length=15, choices=RACE_MODALITY_CHOICES)
    organizer = models.ForeignKey(
        null=True, blank=True, default=None,
        to='entities.Entity', on_delete=models.PROTECT,
    )
    metadata = JSONField(
        default=default_race_metadata,
        validators=[JSONSchemaValidator(schema=RACE_METADATA_SCHEMA)],
    )

    def __str__(self):
        league = f'({self.league.symbol})' if self.league else ''
        return f'{self.date} :: {self.name} {league}'.strip()

    @property
    def is_female(self):
        return (self.league and self.league.gender == LEAGUE_GENDER_FEMALE) or self.gender == LEAGUE_GENDER_FEMALE

    @property
    def name(self) -> str:
        day = f'XORNADA {self.day}' if self.day > 1 else ''
        gender = f'(FEMENINA)' if self.is_female else ''
        modality = f'(VETERANOS)' if self.modality == RACE_VETERANS else ''

        trophy = f'{int_to_roman(self.trophy_edition)} - {self.trophy}' if self.trophy else ''
        flag = f'{int_to_roman(self.flag_edition)} - {self.flag}' if self.flag else ''
        name = ' - '.join([i for i in [trophy, flag, self.sponsor] if i])
        return whitespaces_clean(f'{name} {day} {gender} {modality}')

    def validate_editions(self):
        """
        Validate trophy and flag should have editions.
        """
        if not all_or_none(self.flag_id, self.flag_edition):
            raise IntegrityError(
                f'Instance needs to have both \'flag\' and \'flag_edition\' filled or empty. '
                f'current: (flag_id:{self.flag_id}, flag_edition:{self.flag_edition})'
            )
        if not all_or_none(self.trophy_id, self.trophy_edition):
            raise IntegrityError(
                f'Instance needs to have both \'trophy\' and \'trophy_edition\' filled or empty. '
                f'current: (trophy_id:{self.trophy_id}, trophy_edition:{self.trophy_edition})'
            )

    def validate_gender(self):
        if len([x for x in [self.league, self.gender] if x]) > 1:
            raise IntegrityError(
                f'Instance needs to have only one value for  \'league\' and \'gender\' filled. '
                f'current: (league:{self.league}, gender:{self.gender})'
            )

    def save(self, *args, **kwargs):
        self.validate_editions()
        self.validate_gender()
        super(Race, self).save(*args, **kwargs)

    class Meta:
        db_table = 'race'
        verbose_name = 'Regata'
        unique_together = [
            ['trophy', 'league', 'trophy_edition', 'modality', 'day'],
            ['flag', 'league', 'flag_edition', 'modality', 'day'],
            ['league', 'date']
        ]
        ordering = ['date', 'league']
