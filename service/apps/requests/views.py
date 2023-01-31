from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.requests.serializers import RequestSerializer


class RequestsView(GenericAPIView):
    """
    post:
    Create a new request.
    """

    serializer_class = RequestSerializer

    @extend_schema(responses={
        201: OpenApiTypes.NONE,
        400: OpenApiTypes.OBJECT,
    })
    def post(self, request):
        req = self.serializer_class(data=request.data)
        req.is_valid(raise_exception=True)

        req.save()

        return Response(status=status.HTTP_201_CREATED)
