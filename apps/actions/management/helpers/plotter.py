import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import MultipleLocator

from apps.entities.models import Entity, League
from apps.participants.services import ParticipantService
from apps.races.models import Flag
from rscraping.data.constants import CATEGORY_ABSOLUT, GENDER_MALE


class Plotter:
    BOXPLOT = "boxplot"
    LINE = "line"
    NTH_SPEED = "nth"

    @classmethod
    def types(cls) -> list[str]:
        return [cls.BOXPLOT, cls.LINE, cls.NTH_SPEED]

    def __init__(self, plot_type: str, normalized: bool = False):
        self._plot_type = plot_type
        self._normalized = normalized

    def label(
        self,
        index: int | None = None,
        club: Entity | None = None,
        league: League | None = None,
    ) -> str:
        label = "VELOCIDADES (km/h)"

        if league and club:
            label = f"{club.name} ({league.symbol}) {label}"
        elif club:
            label = f"{club.name} {label}"
        elif league:
            label = f"{league.symbol} {label}"

        if index:
            label = f"VELOCIDADES (km/h) del {index}"
            if league:
                label += f" ({league.symbol})"

        if self._normalized:
            label += " - normalizadas"

        return label

    def load_data(
        self,
        index: int | None = None,
        club: Entity | None = None,
        league: League | None = None,
        flag: Flag | None = None,
        years: list[int] | None = None,
        gender: str = GENDER_MALE,
        category: str = CATEGORY_ABSOLUT,
        day: int = 1,
        branch_teams: bool = False,
        only_league_races: bool = False,
    ):
        if self._plot_type in [self.BOXPLOT, self.LINE]:
            self._data = ParticipantService.get_year_speeds_filtered_by(
                club=club,
                league=league,
                flag=flag,
                gender=gender,
                category=category,
                day=day,
                branch_teams=branch_teams,
                only_league_races=only_league_races,
                normalize=self._normalized,
            )
            if years:
                self._data = {year: self._data[year] for year in years}
        elif self._plot_type in [self.NTH_SPEED]:
            assert index and index > 0, f"invalid {index=}"
            assert years, f"invalid {years=}"

            self._data = {
                year: ParticipantService.get_nth_speed_filtered_by(
                    index=index,
                    club=club,
                    league=league,
                    gender=gender,
                    category=category,
                    year=int(year),
                    day=day,
                    branch_teams=branch_teams,
                    only_league_races=only_league_races,
                    normalize=self._normalized,
                )
                for year in years
            }
        else:
            raise ValueError(f"invalid {self._plot_type=}")

    def plot(self, label: str):
        if self._plot_type in [Plotter.BOXPLOT]:
            _, ax = plt.subplots()
            self._boxplot(ax, label)
        elif self._plot_type in [Plotter.LINE, Plotter.NTH_SPEED]:
            self._lineplot(label)
        else:
            raise ValueError(f"invalid {self._plot_type=}")

    def save(self, path: str | None):
        if path:
            plt.savefig(path)
        else:
            plt.show()

    def _boxplot(self, ax: Axes, label: str):
        ax.set_title(label)
        ax.boxplot(list(self._data.values()))
        ax.set_xticklabels([str(k) for k in self._data.keys()])

        plt.gca().yaxis.set_major_locator(MultipleLocator(0.5))
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="center")

    def _lineplot(self, label: str):
        for k in self._data.keys():
            plt.plot(range(1, len(self._data[k]) + 1), self._data[k], label=f"{k}")

        plt.xlabel("Regata")
        plt.xticks(range(1, max(len(e) for e in self._data.values()) + 1, 1))
        plt.ylabel("Velocidad (km/h)")
        plt.title(label)
        plt.legend()
