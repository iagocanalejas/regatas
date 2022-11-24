from rest_framework import serializers

from ai_django.ai_core.utils.shortcuts import get_model, get_object_or_none
from apps.requests.models import Request, REQUEST_UPDATE


class RequestSerializer(serializers.ModelSerializer):
    def validate_target_id(self, target_id):
        if self.initial_data['type'] == REQUEST_UPDATE and not get_object_or_none(get_model(self.initial_data['model']), pk=target_id):
            # verify the target updated exists
            raise serializers.ValidationError(f"Target should be an existing database object")

        return target_id

    class Meta:
        model = Request
        read_only_fields = ('id',)
        fields = ('model', 'target_id', 'type', 'changes')
