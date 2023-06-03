from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.entities.serializers import ParticipationSerializer
from apps.entities.services import LeagueService, EntityService
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from apps.serializers import LeagueSerializer, ClubSerializer, OrganizerSerializer, EntitySerializer
from utils.choices import ENTITY_CLUB, ENTITY_LEAGUE, ENTITY_FEDERATION, ENTITY_PRIVATE


class LeaguesView(APIView):
    """
    get:
    Return a list of active leagues
    """
    @staticmethod
    @extend_schema(responses={200: LeagueSerializer(many=True)})
    def get(request):
        return Response(LeagueSerializer(LeagueService.get_with_parent(), many=True).data, status=status.HTTP_200_OK)


class ClubsView(APIView):
    """
    get:
    Return a list of active clubs
    """
    @staticmethod
    @extend_schema(responses={200: ClubSerializer(many=True)})
    def get(request):
        # TODO: Exclude clubs without participation
        clubs = EntityService.get_clubs()
        return Response(ClubSerializer(clubs, many=True).data, status=status.HTTP_200_OK)


class ClubView(APIView):
    """
    get:
    Return an active club
    """
    @staticmethod
    @extend_schema(responses={200: ClubSerializer()})
    def get(request, club_id: int):
        club = EntityService.get_club_by_id(club_id)
        return Response(ClubSerializer(club).data, status=status.HTTP_200_OK)


class OrganizersView(APIView):
    """
    get:
    Return a list of active organizers
    """
    @staticmethod
    @extend_schema(responses={200: OrganizerSerializer(many=True)})
    def get(request):
        entities = EntityService.get()
        return Response(
            {
                'clubs': ClubSerializer([e for e in entities if e.type == ENTITY_CLUB], many=True).data,
                'leagues': EntitySerializer([e for e in entities if e.type == ENTITY_LEAGUE], many=True).data,
                'federations': EntitySerializer([e for e in entities if e.type == ENTITY_FEDERATION], many=True).data,
                'private': EntitySerializer([e for e in entities if e.type == ENTITY_PRIVATE], many=True).data,
            },
            status=status.HTTP_200_OK
        )


class ClubRacesView(GenericAPIView):
    """
    get:
    Return an active club races
    """
    queryset = Participant.objects
    serializer_class = ParticipationSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='trophy', description='Filter by trophy', required=False, type=int),
            OpenApiParameter(name='flag', description='Filter by flag', required=False, type=int),
            OpenApiParameter(name='league', description='Filter by league', required=False, type=int),
            OpenApiParameter(name='year', description='Filter by year', required=False, type=int),
            OpenApiParameter(name='keywords', description='Filter by trophy, flag, league, sponsor, town', required=False, type=str),
            OpenApiParameter(name='gender', description='Filter by gender', required=False, type=str),
            OpenApiParameter(name='category', description='Filter by category', required=False, type=str),
            OpenApiParameter(name='ordering', description='Sort results by given param. default: #Race.date', required=False, type=str),
        ],
        responses={
            200: ParticipationSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, club_id: int):
        queryset = self.get_queryset().filter(club_id=club_id)
        races = ParticipantService.get_filtered(
            queryset,
            request.query_params,
            related=['race', 'race__trophy', 'race__flag', 'race__league', 'race__organizer'],
            prefetch=['race__participants']
        )
        page = self.paginate_queryset(races)
        if page is not None:
            return self.get_paginated_response(ParticipationSerializer(page, many=True).data)
        return Response(ParticipationSerializer(races, many=True).data, status=status.HTTP_200_OK)
