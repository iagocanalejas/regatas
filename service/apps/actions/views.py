from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.actions.clients import Client
from apps.actions.datasource import Datasource
from apps.actions.serializers import ScrapActionSerializer, ScrappedRaceSerializer, ActionScrapSerializer


class ScrapActionView(APIView):
    serializer_class = ScrapActionSerializer

    @extend_schema(responses={
        200: ActionScrapSerializer,
        400: OpenApiTypes.OBJECT,
    })
    def post(self, request):
        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)

        result = []
        data = data.validated_data
        datasource = data.get('datasource').lower()

        if datasource not in [Datasource.ACT, Datasource.ARC, Datasource.LGT]:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"datasource": ["A valid datasource is required."]})

        client: Client = Client(source=datasource)
        if data.get('race_id', False):
            db_race, db_participants = client.get_db_race_by_id(data.get('race_id'))
            web_race, web_participants = client.get_web_race_by_id(data.get('race_id'), is_female=data.get('is_female', False))
            serializer = ActionScrapSerializer(
                {
                    'db_race': db_race,
                    'web_race': web_race
                },
                context={
                    'db_participants': db_participants,
                    'web_participants': web_participants
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(ScrappedRaceSerializer(result, many=True).data, status=status.HTTP_200_OK)
