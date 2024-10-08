#!/usr/bin/env python

import logging
from dataclasses import dataclass, field
from typing import override

from django.core.management import BaseCommand

from apps.actions.management.helpers.plotter import Plotter
from apps.entities.models import Entity, League
from apps.entities.services import EntityService
from apps.races.models import Flag
from apps.races.services import FlagService
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


class Command(BaseCommand):
    help = """
    Plot statistics of the races given a set of filters.
    """

    @override
    def add_arguments(self, parser):
        parser.add_argument("type", type=str, nargs="?", default=Plotter.BOXPLOT, help=f"plot type {Plotter.types()}.")

        parser.add_argument("-i", "--index", type=int, help="position to plot the speeds in 'nth' charts.")
        parser.add_argument("-c", "--club", type=int, help="club ID for which to load the data.")
        parser.add_argument("-l", "--league", type=int, help="league ID for which to load the data.")
        parser.add_argument("-f", "--flag", type=int, help="flagID for which to load the data.")
        parser.add_argument("-g", "--gender", type=str, default=GENDER_MALE, help="gender filter.")
        parser.add_argument("-ca", "--category", type=str, default=CATEGORY_ABSOLUT, help="category filter.")
        parser.add_argument("-y", "--years", type=int, nargs="*", default=[], help="years to include in the data.")
        parser.add_argument("-d", "--day", type=int, default=1, help="day of the race for multiday races.")

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
        plotter = Plotter(plot_type=config.plot_type, normalized=config.normalize)

        label = plotter.label(
            index=config.index,
            club=config.club,
            league=config.league,
        )

        plotter.load_data(
            index=config.index,
            club=config.club,
            league=config.league,
            flag=config.flag,
            years=config.years,
            gender=config.gender,
            category=config.category,
            branch_teams=config.branch_teams,
            only_league_races=config.only_league_races,
        )

        plotter.plot(label)
        plotter.save(config.output_path)


@dataclass
class PlotConfig:
    index: int | None
    club: Entity | None
    league: League | None
    flag: Flag | None

    plot_type: str

    gender: str
    category: str
    normalize: bool = False

    only_league_races: bool = False
    branch_teams: bool = False

    years: list[int] = field(default_factory=list)
    day: int = 1

    output_path: str | None = None

    @classmethod
    def from_args(cls, **options) -> "PlotConfig":
        index, club_id, league_id, flag_id, plot_type, gender, category = (
            options["index"],
            options["club"],
            options["league"],
            options["flag"],
            options["type"],
            options["gender"].upper(),
            options["category"].upper(),
        )

        only_league_races, branch_teams, normalize, years, day, output_path = (
            options["leagues_only"],
            options["branch_teams"],
            options["normalize"],
            options["years"],
            options["day"],
            options["output"],
        )

        assert not gender or gender in [GENDER_MALE, GENDER_FEMALE, GENDER_ALL, GENDER_MIX], f"invalid {gender=}"
        assert not category or category in [CATEGORY_ABSOLUT, CATEGORY_SCHOOL, CATEGORY_VETERAN], f"invalid {category=}"
        assert not plot_type or plot_type in [Plotter.BOXPLOT, Plotter.LINE, Plotter.NTH_SPEED], f"invalid {plot_type=}"
        assert plot_type != Plotter.NTH_SPEED or years, f"{plot_type=} requires at least one {years=}"
        assert plot_type != Plotter.NTH_SPEED or index, f"{plot_type=} requires an {index=}"

        club = EntityService.get_entity_or_none(club_id) if club_id else None
        assert not club_id or club, f"invalid {club_id=}"

        flag = FlagService.get_flag_or_none(flag_id) if flag_id else None
        assert not flag_id or flag, f"invalid {flag_id=}"

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
            index=index,
            club=club,
            league=league,
            flag=flag,
            plot_type=plot_type,
            gender=gender,
            category=category,
            only_league_races=only_league_races,
            branch_teams=branch_teams,
            normalize=normalize,
            years=years,
            day=day,
            output_path=output_path,
        )
