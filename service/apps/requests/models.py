from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField

from ai_django.ai_core.models import CreationStampModel
from ai_django.ai_core.validators import JSONSchemaValidator
from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.races.models import Race
from apps.requests.schemas import KEY_VALUE_SCHEMA

REQUEST_CREATE = 'CREATE'
REQUEST_UPDATE = 'UPDATE'
RACE_REQUEST = Race.__name__
PARTICIPANT_REQUEST = Participant.__name__
ENTITY_REQUEST = Entity.__name__

REQUEST_TYPES = [REQUEST_CREATE, REQUEST_UPDATE]
REQUEST_MODELS = [RACE_REQUEST, PARTICIPANT_REQUEST, ENTITY_REQUEST]

REQUEST_TYPE_CHOICES = [(REQUEST_CREATE, 'Crear'), (REQUEST_UPDATE, 'Actualizar')]
REQUEST_MODEL_CHOICES = [(RACE_REQUEST, 'Regata'), (PARTICIPANT_REQUEST, 'Participación'), (ENTITY_REQUEST, 'Club')]


class Request(CreationStampModel):
    model = models.CharField(max_length=50, choices=REQUEST_MODEL_CHOICES)
    target_id = models.PositiveIntegerField(null=True, blank=True, default=None)

    type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)

    changes = ArrayField(
        base_field=JSONField(
            default=dict,
            validators=[JSONSchemaValidator(schema=KEY_VALUE_SCHEMA)],
        ), default=list
    )

    class Meta:
        db_table = 'request'
        verbose_name = 'Petición'
        verbose_name_plural = 'Peticiones'
