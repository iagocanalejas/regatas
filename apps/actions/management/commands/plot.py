#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import override

import matplotlib.pyplot as plt
from django.core.management import BaseCommand
from matplotlib.ticker import MultipleLocator

from apps.entities.models import Entity
from apps.entities.services import EntityService
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from rscraping.data.constants import GENDER_FEMALE, GENDER_MALE

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @staticmethod
    def speed(participant: Participant) -> float:
        assert participant.distance
        assert len(participant.laps) > 0

        time = participant.laps[-1]
        duration = timedelta(minutes=time.minute, seconds=time.second, microseconds=time.microsecond)
        return (participant.distance / duration.total_seconds()) * 3.6

    @override
    def add_arguments(self, parser):
        parser.add_argument("club", type=int, help="club ID to filter participants.")

        parser.add_argument("-f", "--female", action="store_true", default=False, help="female races.")
        parser.add_argument("--leagues-only", action="store_true", default=False, help="only races from a league.")
        parser.add_argument("--branch-teams", action="store_true", default=False, help="filter only branch teams.")

    @override
    def handle(self, *_, **options):
        logger.info(f"{options}")
        config = PlotConfig.from_args(**options)
        speeds = ParticipantService.get_year_speeds_by_club(
            config.club,
            config.gender,
            config.branch_teams,
            config.only_league_races,
        )

        _, ax = plt.subplots()
        ax.set_title("Speeds by Year")
        ax.boxplot(speeds.values())
        ax.set_xticklabels(speeds.keys())

        plt.gca().yaxis.set_major_locator(MultipleLocator(0.5))

        plt.show()


@dataclass
class PlotConfig:
    club: Entity
    gender: str

    only_league_races: bool = False
    branch_teams: bool = False

    @classmethod
    def from_args(cls, **options) -> "PlotConfig":
        club_id, is_female, only_league_races, branch_teams = (
            options["club"],
            options["female"],
            options["leagues-only"],
            options["branch-teams"],
        )

        if not club_id:
            raise ValueError("required value for 'club_id'")
        club = EntityService.get_entity_or_none(club_id)
        if club_id and not club:
            raise ValueError(f"invalid {club_id=}")
        assert club

        return cls(
            club=club,
            gender=GENDER_FEMALE if is_female else GENDER_MALE,
            only_league_races=only_league_races,
            branch_teams=branch_teams,
        )
