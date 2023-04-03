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
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

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
    name = models.CharField(unique=True, max_length=150)
    official_name = models.CharField(unique=True, max_length=150)
    other_names = ArrayField(default=list, blank=True, base_field=models.CharField(max_length=150))

    type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    symbol = models.CharField(null=True, blank=True, default=None, max_length=10)
    title = models.ForeignKey(
        null=True,
        default=None,
        to='EntityTitle',
        on_delete=models.PROTECT,
        related_name='entities',
        related_query_name='entity',
    )
    metadata = JSONField(
        default=default_metadata,
        validators=[JSONSchemaValidator(schema=METADATA_SCHEMA)],
    )

    def __str__(self):
        if self.title:
            return f'{self.name} {self.title.name}' if self.title.show_after else f'{self.title.name} {self.name}'
        return self.name

    @staticmethod
    def queryset_for_search() -> QuerySet:
        """
        :return: #QuerySet annotated for named search
        """
        return Entity.objects.annotate(
            joined_names=Func(F('other_names'), Value(' '), function='array_to_string', output_field=models.CharField())
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Entity, self).save(*args, **kwargs)

    class Meta:
        db_table = 'entity'
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        ordering = ['type', 'name']


class EntityTitle(models.Model):
    name = models.CharField(unique=True, max_length=150)
    show_after = models.BooleanField(default=False)

    class Meta:
        db_table = 'entity_tite'
        verbose_name = 'Titulo'
        ordering = ['name']
