import logging
import os

from django.conf import settings
from django.contrib import admin
from django.db.models import JSONField
from django.http import HttpResponseRedirect
from django.utils import timezone
from prettyjson import PrettyJSONWidget

from ai_django.ai_core.admin import StampedModelAdmin
from apps.actions.models import Task, STATUS_ERROR, STATUS_SUCCESS
from apps.participants.models import Participant
from apps.races.models import Race

logger = logging.getLogger(__name__)


class TaskAdmin(StampedModelAdmin):
    change_form_template = os.path.join(settings.TEMPLATES_ROOT, 'admin', 'task_changeform.html')

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    def response_change(self, request, task: Task):
        if "_cancel-task" in request.POST:
            task.status = STATUS_ERROR
            task.resolved_date = timezone.now()
            task.save()

            logger.info(f'cancelled {task=}')
            self.message_user(request, 'Task cancelled')
            return HttpResponseRedirect(".")

        if "_approve-task" in request.POST:
            race = Race(**task.details['race'])
            race.save()
            logger.info(f'created {race=}')

            participants = [Participant(**p, race=race) for p in task.details['participants']]
            Participant.objects.bulk_create(participants)
            logger.info(f'created participants {participants=}')

            task.status = STATUS_SUCCESS
            task.resolved_date = timezone.now()
            task.save()

            logger.info(f'resolved {task=}')
            self.message_user(request, f'Race {race.id} created with {len(participants)} participants')
            return HttpResponseRedirect(".")

        return super(TaskAdmin, self).response_change(request, task)


admin.site.register(Task, TaskAdmin)
