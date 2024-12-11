from typing import TYPE_CHECKING, Any

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models
from django.db.models import JSONField

from apps.schemas import PARTICIPANT_METADATA_SCHEMA, default_metadata
from apps.utils.choices import (
    CATEGORY_ABSOLUT,
    ENTITY_CLUB,
    GENDER_CHOICES,
    GENDER_MALE,
    PARTICIPANT_CATEGORIES_CHOICES,
    PENALTY_CHOICES,
)
from djutils.validators import JSONSchemaValidator
from rscraping.data.models import Datasource


class Participant(models.Model):
    club_names = ArrayField(blank=True, default=list, base_field=models.CharField(max_length=150))
    branch = models.CharField(null=True, blank=True, default=None, max_length=1)
    club = models.ForeignKey(
        null=False,
        to="entities.Entity",
        on_delete=models.CASCADE,
        related_name="participation",
        related_query_name="participation",
        limit_choices_to={"type": ENTITY_CLUB},
    )
    race = models.ForeignKey(
        null=False,
        to="races.Race",
        on_delete=models.CASCADE,
        related_name="participants",
        related_query_name="participant",
    )

    distance = models.PositiveIntegerField(null=True, blank=True, default=None)
    laps = ArrayField(blank=True, default=list, base_field=models.TimeField(null=False))
    lane = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    series = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    handicap = models.TimeField(null=True, blank=True, default=None)

    gender = models.CharField(default=GENDER_MALE, max_length=10, choices=GENDER_CHOICES)
    category = models.CharField(
        default=CATEGORY_ABSOLUT,
        max_length=10,
        choices=PARTICIPANT_CATEGORIES_CHOICES,
    )

    guest = models.BooleanField(default=False)
    absent = models.BooleanField(default=False)
    retired = models.BooleanField(default=False)

    metadata = JSONField(
        default=default_metadata,
        validators=[JSONSchemaValidator(schema=PARTICIPANT_METADATA_SCHEMA)],
    )

    if TYPE_CHECKING:
        # Annotate reverse ForeignKey relationships in TYPE_CHECKING block
        penalties: models.QuerySet["Penalty"]

    def __str__(self):
        branch_info = f" {self.branch}" if self.branch else ""
        return f"{self.club}{branch_info} ({self.gender}) ({self.category})"

    def validate_unique(self, *args, **kwargs):
        """
        Validate a club can't participate twice in a race unless it's in different leagues.
        """
        if self.race and self.race.league:
            query = self.__class__.objects.filter(
                race__league__isnull=False,
                race__league_id=self.race.league_id,
                club_id=self.club.pk,
                race_id=self.race.pk,
            )
            if query.exists():
                raise IntegrityError(
                    f"Instance with club:{self.club.pk}, race:{self.race.pk} and "
                    f"league:{self.race.league.pk} already exists.",
                )

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.validate_unique()

        super().save(*args, **kwargs)

    def get_datasources(self, datasource: Datasource) -> list[dict[str, Any]]:
        datasource_str = datasource.value.lower()
        datasources = self.metadata["datasource"]
        return [d for d in datasources if d["datasource_name"] == datasource_str]

    def add_metadata(self, new: dict[str, Any]) -> "Participant":
        datasource = Datasource(new["datasource_name"])
        assert self.get_datasources(datasource) == [], "datasource already exists"

        self.metadata["datasource"].append(new)
        return self

    class Meta:
        db_table = "participant"
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ["race", "club"]


class Penalty(models.Model):
    penalty = models.PositiveIntegerField(blank=True, default=0)
    disqualification = models.BooleanField(default=False)
    reason = models.CharField(null=True, blank=True, default=None, max_length=500, choices=PENALTY_CHOICES)
    participant = models.ForeignKey(
        null=False,
        to=Participant,
        on_delete=models.CASCADE,
        related_name="penalties",
        related_query_name="penalty",
    )
    notes = ArrayField(blank=True, default=list, base_field=models.TextField())

    def __str__(self):
        if self.disqualification:
            return f"Disqualified: {self.participant}"
        return f"Penalty ({self.reason}: {self.penalty}) -> {self.participant}"

    class Meta:
        db_table = "penalty"
        verbose_name = "Penalización"
        verbose_name_plural = "Penalizaciones"
        ordering = ["participant"]
