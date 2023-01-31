from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.participants.services import ParticipantService
from apps.races.models import Race
from apps.races.serializers import TrophySerializer, FlagSerializer, SimpleRaceSerializer, RaceParamsSerializer, \
    RaceDetailsSerializer, RaceParticipantSerializer
from apps.races.services import FlagService, TrophyService, RaceService


class TrophiesView(APIView):
    """
    get:
    Return a list of active trophies
    """
    @staticmethod
    @extend_schema(responses={200: TrophySerializer(many=True)})
    def get(request):
        return Response(TrophySerializer(TrophyService.get(), many=True).data, status=status.HTTP_200_OK)


class FlagsView(APIView):
    """
    get:
    Return a list of active flags
    """
    @staticmethod
    @extend_schema(responses={200: FlagSerializer(many=True)})
    def get(request):
        return Response(FlagSerializer(FlagService.get(), many=True).data, status=status.HTTP_200_OK)


class RacesView(GenericAPIView):
    """
    get:
    Return Page of races.
    """
    queryset = Race.objects
    serializer_class = SimpleRaceSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='trophy', description='Filter by trophy', required=False, type=int),
            OpenApiParameter(name='flag', description='Filter by flag', required=False, type=int),
            OpenApiParameter(name='league', description='Filter by league', required=False, type=int),
            OpenApiParameter(name='year', description='Filter by year', required=False, type=int),
            OpenApiParameter(name='participant_club', description='Filter by participant club', required=False, type=int),
            OpenApiParameter(name='keywords', description='Filter by trophy, flag, league, sponsor, town', required=False, type=str),
        ],
        responses={
            200: SimpleRaceSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request):
        data = RaceParamsSerializer(data=request.query_params)
        if not data.is_valid():
            return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)

        races = RaceService.get_filtered(self.get_queryset(), data.validated_data, related=['trophy', 'flag', 'league'])
        page = self.paginate_queryset(races)
        if page is not None:
            serialized_races = SimpleRaceSerializer(page, many=True)
            return self.get_paginated_response(serialized_races.data)
        serialized_races = SimpleRaceSerializer(races, many=True)
        return Response(serialized_races.data, status=status.HTTP_200_OK)


class RaceView(APIView):
    """
    get:
    Return a race with its details
    """
    @staticmethod
    @extend_schema(responses={200: RaceDetailsSerializer()})
    def get(request, race_id: int):
        race = RaceService.get_by_id(
            race_id=race_id,
            related=['trophy', 'flag', 'league', 'organizer__title'],
            prefetch=['participants'],
        )
        return Response(RaceDetailsSerializer(race).data, status=status.HTTP_200_OK)


class RaceParticipantsView(APIView):
    """
    get:
    Return a list of race participants
    """
    @staticmethod
    @extend_schema(responses={200: RaceParticipantSerializer(many=True)})
    def get(request, race_id: int):
        participants = ParticipantService.get_by_race_id(race_id, related=['club__title'], prefetch=['penalties'])
        return Response(RaceParticipantSerializer(participants, many=True).data, status=status.HTTP_200_OK)
