from django.db import models
from django.db.models import JSONField

from ai_django.ai_core.models import CreationStampModel
from apps.races.models import Race
from utils.choices import GENDER_CHOICES

STATUS_PENDING = 'PENDING'
STATUS_PROCESSED = 'PROCESSED'
STATUS_ERROR = 'ERROR'
STATUS_SUCCESS = 'SUCCESS'
TASK_STATUSES = [
    (STATUS_PENDING, 'PENDING'),
    (STATUS_PROCESSED, 'PROCESSED'),
    (STATUS_ERROR, 'ERROR'),
    (STATUS_SUCCESS, 'SUCCESS'),
]


class Task(CreationStampModel):
    datasource = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    race_id = models.CharField(max_length=15)
    status = models.CharField(max_length=10, default=STATUS_PENDING, choices=TASK_STATUSES)
    processed_date = models.DateTimeField(default=None, null=True, blank=True)
    resolved_date = models.DateTimeField(default=None, null=True, blank=True)
    details = JSONField(default=None, null=True)  # TODO: validation

    def __str__(self):
        return f'{self.datasource}: {self.race_id}'

    class Meta:
        db_table = 'task'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
