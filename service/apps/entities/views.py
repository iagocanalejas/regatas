from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.choices import ENTITY_CLUB, ENTITY_LEAGUE, ENTITY_FEDERATION, ENTITY_PRIVATE
from apps.entities.serializers import LeagueSerializer, ClubSerializer, OrganizerSerializer, EntitySerializer
from apps.entities.services import LeagueService, EntityService


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
        clubs = EntityService.get_clubs(related=['title'])
        return Response(ClubSerializer(clubs, many=True).data, status=status.HTTP_200_OK)


class ClubView(APIView):
    """
    get:
    Return an active club
    """
    @staticmethod
    @extend_schema(responses={200: ClubSerializer()})
    def get(request, club_id: int):
        club = EntityService.get_club_by_id(club_id, related=['title'])
        return Response(ClubSerializer(club).data, status=status.HTTP_200_OK)


class OrganizersView(APIView):
    """
    get:
    Return a list of active organizers
    """
    @staticmethod
    @extend_schema(responses={200: OrganizerSerializer(many=True)})
    def get(request):
        entities = EntityService.get(related=['title'])
        return Response(
            {
                'clubs': ClubSerializer([e for e in entities if e.type == ENTITY_CLUB], many=True).data,
                'leagues': EntitySerializer([e for e in entities if e.type == ENTITY_LEAGUE], many=True).data,
                'federations': EntitySerializer([e for e in entities if e.type == ENTITY_FEDERATION], many=True).data,
                'private': EntitySerializer([e for e in entities if e.type == ENTITY_PRIVATE], many=True).data,
            },
            status=status.HTTP_200_OK
        )
