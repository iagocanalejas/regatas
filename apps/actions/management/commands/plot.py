#!/usr/bin/env python

import logging
from dataclasses import dataclass, field
from typing import override

import matplotlib.pyplot as plt
from django.core.management import BaseCommand
from matplotlib.axes import Axes
from matplotlib.ticker import MultipleLocator

from apps.entities.models import Entity, League
from apps.entities.services import EntityService
from apps.participants.services import ParticipantService
from rscraping.data.constants import (
    CATEGORY_ABSOLUT,
    CATEGORY_SCHOOL,
    CATEGORY_VETERAN,
    GENDER_ALL,
    GENDER_FEMALE,
    GENDER_MALE,
    GENDER_MIX,
)

logger = logging.getLogger(__name__)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

PLOT_BOXPLOT = "boxplot"
PLOT_LINE = "line"


class Command(BaseCommand):
    @override
    def add_arguments(self, parser):
        parser.add_argument("club", nargs="?", type=int, help="club ID to filter participants.")
        parser.add_argument("-l", "--league", type=int, help="league ID for which to plot the data.")

        parser.add_argument("-t", "--type", type=str, default=PLOT_BOXPLOT, help="plot type.")
        parser.add_argument("-g", "--gender", type=str, default=GENDER_MALE, help="races gender.")
        parser.add_argument("-c", "--category", type=str, default=CATEGORY_ABSOLUT, help="races category.")
        parser.add_argument(
            "-n",
            "--normalize",
            action="store_true",
            default=False,
            help="exclude outliers based on the speeds' standard deviation.",
        )

        parser.add_argument("-y", "--years", type=str, nargs="*", default=[], help="years to include in the plot.")
        parser.add_argument("--leagues-only", action="store_true", default=False, help="only races from a league.")
        parser.add_argument("--branch-teams", action="store_true", default=False, help="filter only branch teams.")

        parser.add_argument("-o", "--output", type=str, help="saves the output plot.")

    @override
    def handle(self, *_, **options):
        logger.info(f"{options}")
        config = PlotConfig.from_args(**options)
        speeds = ParticipantService.get_year_speeds_by_club(
            config.club,
            config.league,
            config.gender,
            config.category,
            config.branch_teams,
            config.only_league_races,
            config.normalize,
        )

        if config.years:
            speeds = {int(year): speeds[int(year)] for year in config.years}

        label = "VELOCIDADES (km/h)"
        if config.club:
            label = f"{config.club.name} {label}"
        if config.league:
            label = f"{config.league.symbol} {label}"
        if config.league and config.club:
            label = f"{config.club.name} ({config.league.symbol}) VELOCIDADES (km/h)"

        if config.normalize:
            label = f"{label} - normalizadas"

        if config.plot_type == PLOT_BOXPLOT:
            _, ax = plt.subplots()
            self.boxplot(ax, label, speeds)
        elif config.plot_type == PLOT_LINE:
            self.lineplot(label, speeds)
        else:
            raise ValueError(f"invalid {config.plot_type=}")

        if config.output_path:
            plt.savefig(config.output_path)
        else:
            plt.show()

    def boxplot(self, ax: Axes, label: str, speeds: dict[int, list[float]]):
        ax.set_title(label)
        ax.boxplot(list(speeds.values()))
        ax.set_xticklabels([str(k) for k in speeds.keys()])

        plt.gca().yaxis.set_major_locator(MultipleLocator(0.5))
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="center")

    def lineplot(self, label: str, speeds: dict[int, list[float]]):
        for k in speeds.keys():
            plt.plot(range(1, len(speeds[k]) + 1), speeds[k], label=f"{k}")

        plt.xlabel("Regata")
        plt.xticks(range(1, max(len(e) for e in speeds.values()) + 1, 1))
        plt.ylabel("Velocidad (km/h)")
        plt.title(label)
        plt.legend()


@dataclass
class PlotConfig:
    club: Entity | None
    league: League | None

    plot_type: str

    gender: str
    category: str
    normalize: bool = False

    only_league_races: bool = False
    branch_teams: bool = False

    years: list[str] = field(default_factory=list)

    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "PlotConfig":
        club_id, league_id, plot_type, gender, category = (
            options["club"],
            options["league"],
            options["type"],
            options["gender"].upper(),
            options["category"].upper(),
        )

        only_league_races, branch_teams, normalize, years, output_path = (
            options["leagues_only"],
            options["branch_teams"],
            options["normalize"],
            options["years"],
            options["output"],
        )

        if not gender or gender not in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX]:
            raise ValueError(f"invalid {gender=}")

        if not category or category not in [CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN]:
            raise ValueError(f"invalid {category=}")

        if not plot_type or plot_type not in [PLOT_BOXPLOT, PLOT_LINE]:
            raise ValueError(f"invalid {plot_type=}")

        club = EntityService.get_entity_or_none(club_id) if club_id else None
        if club_id and not club:
            raise ValueError(f"invalid {club_id=}")

        league = League.objects.get(pk=league_id) if league_id else None
        if league and branch_teams:
            logger.warning("branch_teams is not supported with leagues, ignoring it")
            branch_teams = False

        if league and gender != league.gender:
            logger.warning(f"given {gender=} does not match {league.gender}, using league's one")
            gender = league.gender if league.gender else gender

        if league and category != league.category:
            logger.warning(f"given {category=} does not match {league.category}, using league's one")
            category = league.category if league.category else category

        return cls(
            club=club,
            league=league,
            plot_type=plot_type,
            gender=gender,
            category=category,
            only_league_races=only_league_races,
            branch_teams=branch_teams,
            normalize=normalize,
            years=years,
            output_path=output_path,
        )
