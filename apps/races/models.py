import logging

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models
from django.db.models import JSONField
from utils.choices import (
    RACE_CONVENTIONAL,
    RACE_GENDER_CHOICES,
    RACE_MODALITY_CHOICES,
    RACE_TRAINERA,
    RACE_TYPE_CHOICES,
)

from apps.schemas import METADATA_SCHEMA, default_metadata
from djutils.models import CreationStampModel
from djutils.validators import JSONSchemaValidator
from pyutils.shortcuts import all_or_none
from pyutils.strings import int_to_roman, whitespaces_clean
from rscraping import lemmatize

logger = logging.getLogger(__name__)


class Trophy(CreationStampModel):
    name = models.CharField(max_length=150, unique=True)
    tokens = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=50), editable=False)
    verified = models.BooleanField(blank=True, default=False)

    qualifies_for = models.ForeignKey(to="self", null=True, blank=True, default=None, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tokens = list(lemmatize(self.name))
        super().save(*args, **kwargs)

    class Meta(CreationStampModel.Meta):
        db_table = "trophy"
        verbose_name = "Trofeo"
        verbose_name_plural = "Trofeos"
        ordering = ["name"]


class Flag(CreationStampModel):
    name = models.CharField(max_length=150, unique=True)
    tokens = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=50), editable=False)
    verified = models.BooleanField(blank=True, default=False)

    qualifies_for = models.ForeignKey(to="self", null=True, blank=True, default=None, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tokens = list(lemmatize(self.name))
        super().save(*args, **kwargs)

    class Meta(CreationStampModel.Meta):
        db_table = "flag"
        verbose_name = "Bandera"
        verbose_name_plural = "Banderas"
        ordering = ["name"]


# TODO: enum of cancellation reasons
class Race(CreationStampModel):
    laps = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    lanes = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
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
        null=True,
        blank=True,
        default=None,
        to=Trophy,
        on_delete=models.PROTECT,
        related_name="editions",
        related_query_name="edition",
    )
    # 'flag_edition' and 'flag' should both be NULL or NOT_NULL
    flag_edition = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    flag = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to=Flag,
        on_delete=models.PROTECT,
        related_name="editions",
        related_query_name="edition",
    )

    league = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to="entities.League",
        on_delete=models.PROTECT,
        related_name="races",
        related_query_name="race",
    )

    associated = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to="self",
        on_delete=models.PROTECT,
        related_name="+",
    )

    gender = models.CharField(max_length=15, choices=RACE_GENDER_CHOICES)
    modality = models.CharField(default=RACE_TRAINERA, max_length=15, choices=RACE_MODALITY_CHOICES)
    organizer = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to="entities.Entity",
        on_delete=models.PROTECT,
    )
    metadata = JSONField(
        default=default_metadata,
        validators=[JSONSchemaValidator(schema=METADATA_SCHEMA)],
    )

    def __str__(self):
        league = f"({self.league.symbol})" if self.league else ""
        return f"{self.date} :: {self.name} {league}".strip()

    @property
    def name(self) -> str:
        day = f"XORNADA {self.day}" if self.day > 1 else ""

        trophy = f"{int_to_roman(self.trophy_edition)} - {self.trophy}" if self.trophy and self.trophy_edition else ""
        flag = f"{int_to_roman(self.flag_edition)} - {self.flag}" if self.flag and self.flag_edition else ""
        name = " - ".join([i for i in [trophy, flag, self.sponsor] if i])
        return whitespaces_clean(f"{name} {day}")

    def validate_editions(self):
        """
        Validate trophy and flag should have editions.
        """
        if not all_or_none(self.flag, self.flag_edition):
            raise IntegrityError(
                f"Instance needs to have both 'flag' and 'flag_edition' filled or empty. "
                f"current: (flag_id:{self.flag}, flag_edition:{self.flag_edition})"
            )
        if not all_or_none(self.trophy, self.trophy_edition):
            raise IntegrityError(
                f"Instance needs to have both 'trophy' and 'trophy_edition' filled or empty. "
                f"current: (trophy_id:{self.trophy}, trophy_edition:{self.trophy_edition})"
            )

    def validate_associated(self):
        if self.day == 2 and not self.associated:
            raise IntegrityError("Instance needs to have an associated 'race' when 'day' = 2.")

    def save(self, *args, **kwargs):
        self.validate_editions()
        self.validate_associated()
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta(CreationStampModel.Meta):
        db_table = "race"
        verbose_name = "Regata"
        unique_together = [
            ["trophy", "league", "trophy_edition", "modality", "day"],
            ["flag", "league", "flag_edition", "modality", "day"],
            ["league", "date"],
        ]
        ordering = ["date", "league"]
