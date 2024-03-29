from collections.abc import Generator
from typing import Any, Protocol

from apps.entities.models import Entity
from apps.participants.models import Participant
from apps.races.models import Race
from rscraping.clients import ClientProtocol
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace


class IngestorProtocol(Protocol):
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

    def fetch_by_club(self, club: Entity, year: int, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the club and year to filter.

        Args:
            club: Entity: The club to search for.
            year: int: The year to search for.

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

    def ingest(self, race: RSRace, **kwargs) -> tuple[Race, Race | None]:
        """
        Converts the fetched RSRace into a database Race trying to retrieve valid data from the database.

        Args:
            race: RSRace: The race to ingest.

        Returns: tuple[Race, Race | None]:
            Race: The new ingested race.
            Race | None: An associated race if it exists.
        """
        ...

    def merge(self, race: Race, db_race: Race) -> tuple[Race, bool]:
        """
        Merge two races into one.

        Args:
            race Race: The newly ingested race.
            db_race Race: An existing database race.

        Returns: tuple[Race, bool]:
            Race: The merged race result.
            bool: Whether the races were merged or not.
        """
        ...

    def verify(self, race: Race, rs_race: RSRace) -> tuple[Race, bool, bool]:
        """
        Verify all the data in an existing database race matches the scrapped race.
        Will ask to update some fields if needed.

        Args:
            race: Race: The existing database race.
            rs_race: RSRace: The new scrapped data.

        Returns: tuple[Race, bool]:
            Race: The verified race.
            bool: Whether the race was verified or not.
            bool: Whether the race needs to be updated or not.
        """
        ...

    def save(self, race: Race, associated: Race | None = None, **kwargs) -> tuple[Race, bool]:
        """
        Save a new race into the database.

        Args:
            race Race: The race we want to save.
            associated Race | None: An associated race if it exists.

        Returns: tuple[Race, bool]:
            Race: The saved (or not) race.
            bool: Whether the race was saved or not.
        """
        ...

    def ingest_participant(
        self,
        race: Race,
        participant: RSParticipant,
        **kwargs,
    ) -> tuple[Participant, bool]:
        """
        Converts the fetched RSParticipant into a database Participant trying to retrieve valid data from the database.

        Args:
            race Race: The Race to witch the participant belongs.
            participant: RSParticipant: The participant to ingest.

        Returns: tuple[Participant, bool]:
            Participant: The new ingested participant.
            bool: Whether the participant is different from the database one or not.
        """
        ...

    def should_merge_participants(self, participant: Participant, db_participant: Participant) -> bool:
        """
        Check if two participants should be merged.

        Args:
            participant Participant: The newly ingested Participant.
            db_participant Participant: An existing database participant.

        Returns: bool: Whether the participants should be merged or not.
        """
        ...

    def merge_participants(self, participant: Participant, db_participant: Participant) -> tuple[Participant, bool]:
        """
        Merge two participants into one.

        Args:
            participant Participant: The newly ingested Participant.
            db_participant Participant: An existing database participant.

        Returns: tuple[Participant, bool]:
            Participant: The merged participant result.
            bool: Wheter the participants was changed or not.
        """
        ...

    def verify_participants(
        self,
        race: Race,
        participants: list[Participant],
        rs_participants: list[RSParticipant],
    ) -> list[tuple[Participant, bool, bool]]:
        """
        Verify all the data in an existing database participants matches the scrapped participants.

        Args:
            race Race: The Race to witch the participant belongs.
            participants: list[Participant]: The existing database participants.
            rs_participants: list[RSParticipant]: The new scrapped data.

        Returns: list[tuple[Participant, bool]]:
            Participant: The verified participant.
            bool: Whether the participant was verified or not.
            bool: Whether the participant needs to be updated or not.
        """
        ...

    def save_participant(
        self,
        participant: Participant,
        is_disqualified: bool = False,
        **kwargs,
    ) -> tuple[Participant, bool]:
        """
        Save a new participant into the database.

        Args:
            participant Participant: The participant we want to save.
            is_disqualified bool: Whether the participant was disqualified or not.

        Returns: tuple[Participant, bool]:
            Participant: The saved (or not) participant.
            bool: Whether the participant was saved or not.
        """
        ...

    def _get_datasource(self, race: Race, ref_id: str) -> dict | None: ...

    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict: ...

    def _retrieve_race(self, race_id: str) -> Generator[RSRace, Any, Any]: ...
