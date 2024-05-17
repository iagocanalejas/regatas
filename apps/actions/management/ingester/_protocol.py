from collections.abc import Generator
from typing import Any, Protocol

from apps.entities.models import Entity
from rscraping.clients import ClientProtocol
from rscraping.data.models import Race as RSRace


class IngesterProtocol(Protocol):
    client: ClientProtocol

    def fetch(self, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients.

        Yields: RSRace: The races found.
        """
        ...

    def fetch_by_ids(self, race_ids: list[str], **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the IDs to filter.

        Args:
            race_ids: list[str]: The list of IDs to search for.

        Yields: RSRace: The races found.
        """
        ...

    def fetch_by_entity(self, entity: Entity, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the entity and year to filter.

        Args:
            entity: Entity: The club to search for.
            year: int: The year to search for.

        Yields: RSRace: The races found.
        """
        ...

    def fetch_by_club(self, club_id: str, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the club and year to filter.

        Args:
            club_id: str: The club ID to search for.
            year: int: The year to search for.

        Yields: RSRace: The found races.
        """
        ...

    def fetch_by_flag(self, flag_id: str, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the flag to filter.

        Args:
            flag_id: str: The flag to search for.

        Yields: RSRace: The races found.
        """
        ...

    def fetch_by_url(self, url: str, **_) -> RSRace | None:
        """
        Fetch race by given URL.

        Args:
            url: str: The URL to search for.

        Returns: RSRace | None: The found race.
        """
        ...

    def _retrieve_race(self, race_id: str) -> Generator[RSRace, Any, Any]: ...
