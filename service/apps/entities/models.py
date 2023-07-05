from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import QuerySet, Func, F, Value, JSONField

from ai_django.ai_core.models import TraceableModel
from ai_django.ai_core.validators import JSONSchemaValidator
from apps.schemas import default_metadata, METADATA_SCHEMA
from utils.choices import ENTITY_TYPE_CHOICES, GENDER_MALE, GENDER_FEMALE, GENDER_CHOICES


class League(TraceableModel):
    name = models.CharField(unique=True, max_length=150)
    symbol = models.CharField(max_length=10)
    parent = models.ForeignKey('self', null=True, default=None, on_delete=models.PROTECT)
    gender = models.CharField(max_length=10, null=True, default=None, choices=GENDER_CHOICES)

    def __str__(self):
        return self.name

    @property
    def is_male(self):
        return self.gender == GENDER_MALE

    @property
    def is_female(self):
        return self.gender == GENDER_FEMALE

    class Meta:
        db_table = 'league'
        verbose_name = 'Liga'
        ordering = ['id']


class Entity(TraceableModel):
    """
    cases:
        - normal entity. ex: PUEBLA
        - inactive entity that fused into another one. ex: BERMEO -> URDAIBAI
        - subsidiary entity of another club. ex: MEIRA -> SAMERTOLAMEU
    """

    name = models.CharField(unique=True, max_length=150)
    normalized_name = models.CharField(max_length=150)  # not unique | EX: CR BADALONA and CN BADALONA will resolve to BADALONA
    known_names = ArrayField(default=list, blank=True, base_field=models.CharField(max_length=150))

    type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    symbol = models.CharField(null=True, blank=True, default=None, max_length=10)

    is_partnership = models.BooleanField(null=False, blank=True, default=False, db_index=True)

    parent = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to='self',
        on_delete=models.PROTECT,
        related_name='subsidiaries',
        related_query_name='subsidiary',
    )
    fused_into = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to='self',
        on_delete=models.PROTECT,
        related_name='formed_by',
        related_query_name='formed_by',
    )

    metadata = JSONField(
        default=default_metadata,
        validators=[JSONSchemaValidator(schema=METADATA_SCHEMA)],
    )

    def __str__(self):
        return self.name

    @staticmethod
    def queryset_for_search() -> QuerySet:
        """
        :return: #QuerySet annotated for named search
        """
        return Entity.objects.annotate(
            joined_names=Func(F('known_names'), Value(' '), function='array_to_string', output_field=models.CharField())
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Entity, self).save(*args, **kwargs)

    class Meta:
        db_table = 'entity'
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        ordering = ['type', 'name']


class EntityPartnership(models.Model):
    target = models.ForeignKey(
        to='entities.Entity',
        on_delete=models.PROTECT,
        related_name='components',
        related_query_name='component',
        limit_choices_to={"is_partnership", True},
    )
    part = models.ForeignKey(
        to='entities.Entity',
        on_delete=models.PROTECT,
        related_name='part_of',
        related_query_name='part_of',
        limit_choices_to={"is_partnership", False},
    )
    is_active = models.BooleanField(null=False, blank=True, default=True, db_index=True)

    class Meta:
        db_table = 'entity_partnership'
        verbose_name = 'Fusión'
        verbose_name_plural = 'Fusiones'
