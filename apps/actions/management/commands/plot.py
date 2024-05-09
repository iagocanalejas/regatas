#!/usr/bin/env python3

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import override

import matplotlib.pyplot as plt
from django.core.management import BaseCommand
from matplotlib.ticker import MultipleLocator

from apps.entities.models import Entity, League
from apps.entities.services import EntityService
from apps.participants.models import Participant
from apps.participants.services import ParticipantService
from rscraping.data.constants import GENDER_ALL, GENDER_FEMALE, GENDER_MALE, GENDER_MIX

logger = logging.getLogger(__name__)
logging.getLogger("matplotlib").setLevel(logging.WARNING)


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
        parser.add_argument("club", nargs="?", type=int, help="club ID to filter participants.")
        parser.add_argument("-l", "--league", type=int, help="league ID for which to plot the data.")

        parser.add_argument("-g", "--gender", type=str, default=GENDER_MALE, help="races gender.")
        parser.add_argument("--leagues-only", action="store_true", default=False, help="only races from a league.")
        parser.add_argument("--branch-teams", action="store_true", default=False, help="filter only branch teams.")
        parser.add_argument(
            "-n",
            "--normalize",
            action="store_true",
            default=False,
            help="exclude outliers based on the speeds' standard deviation.",
        )

        parser.add_argument("-o", "--output", type=str, help="saves the output plot.")

    @override
    def handle(self, *_, **options):
        logger.info(f"{options}")
        config = PlotConfig.from_args(**options)
        speeds = ParticipantService.get_year_speeds_by_club(
            config.club,
            config.league,
            config.gender,
            config.branch_teams,
            config.only_league_races,
            config.normalize,
        )

        label = "VELOCIDADES (km/h)"
        if config.club:
            label = f"{config.club.name} {label}"
        if config.league:
            label = f"{config.league.symbol} {label}"

        if config.normalize:
            label = f"{label} - normalized"

        _, ax = plt.subplots()
        ax.set_title(label)
        ax.boxplot(speeds.values())
        ax.set_xticklabels(speeds.keys())

        plt.gca().yaxis.set_major_locator(MultipleLocator(0.5))
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="center")

        if config.output_path:
            plt.savefig(config.output_path)
        else:
            plt.show()


@dataclass
class PlotConfig:
    club: Entity | None
    league: League | None
    gender: str

    only_league_races: bool = False
    branch_teams: bool = False
    normalize: bool = False

    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "PlotConfig":
        club_id, league_id, gender, only_league_races, branch_teams, normalize, output_path = (
            options["club"],
            options["league"],
            options["gender"],
            options["leagues_only"],
            options["branch_teams"],
            options["normalize"],
            options["output"],
        )

        if not gender or gender.upper() not in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX]:
            raise ValueError(f"invalid {gender=}")

        club = EntityService.get_entity_or_none(club_id) if club_id else None
        if club_id and not club:
            raise ValueError(f"invalid {club_id=}")

        league = League.objects.get(pk=league_id) if league_id else None
        if league and branch_teams:
            logger.warning("branch_teams is not supported with leagues, ignoring it")
            branch_teams = False

        if gender and league and gender.upper() != league.gender:
            logger.warning(f"given {gender=} does not match {league.gender}, using league's one")
            gender = league.gender if league.gender else gender

        return cls(
            club=club,
            league=league,
            gender=gender.upper(),
            only_league_races=only_league_races,
            branch_teams=branch_teams,
            normalize=normalize,
            output_path=output_path,
        )
