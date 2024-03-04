from collections.abc import Generator
from typing import Any, Protocol

from apps.participants.models import Participant
from apps.races.models import Race
from rscraping import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Race as RSRace


class IngestorProtocol(Protocol):
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
    ) -> Participant:
        """
        Converts the fetched RSParticipant into a database Participant trying to retrieve valid data from the database.

        Args:
            race Race: The Race to witch the participant belongs.
            participant: RSParticipant: The participant to ingest.

        Returns: Participant: The new ingested participant.
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
            bool: Wheter the participants were merged or not.
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

    @staticmethod
    def _validate_datasource_and_build_metadata(race: RSRace, datasource: Datasource) -> dict: ...
