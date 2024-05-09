from collections.abc import Generator
from enum import Enum, auto
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

    class Status(Enum):
        IGNORE = auto()
        EXISTING = auto()

        NEW = auto()
        MERGED = auto()

        CREATED = auto()
        UPDATED = auto()

        def next(self) -> "IngestorProtocol.Status":
            if self == self.NEW:
                return self.CREATED
            if self == self.MERGED:
                return self.UPDATED
            return self

        def is_saved(self) -> bool:
            return self in [self.CREATED, self.UPDATED]

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

    def fetch_by_flag(self, flag: str, **kwargs) -> Generator[RSRace, Any, Any]:
        """
        Fetch races that should be ingested from one of many clients using the flag to filter.

        Args:
            flag: str: The flag to search for.

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

    def ingest(self, race: RSRace, **kwargs) -> tuple[Race, Race | None, Status]:
        """
        Converts the fetched RSRace into a database Race trying to retrieve valid data from the database.

        Args:
            race: RSRace: The race to ingest.

        Returns: tuple[Race, Race | None]:
            Race: The new ingested race.
            Race | None: An associated race if it exists.
            RaceDigestionStatus: The status of the race after ingestion.
        """
        ...

    def merge(self, race: Race, db_race: Race, status: Status) -> tuple[Race, Status]:
        """
        Merge two races into one.

        Args:
            race Race: The newly ingested race.
            db_race Race: An existing database race.
            status RaceDigestionStatus: The status of the race.

        Returns: tuple[Race, bool]:
            Race: The merged race result.
            RaceDigestionStatus: The status of race after the merge.
        """
        ...

    def save(self, race: Race, status: Status, associated: Race | None = None, **kwargs) -> tuple[Race, Status]:
        """
        Save a new race into the database.

        Args:
            race Race: The race we want to save.
            status RaceDigestionStatus: The status of the race.
            associated Race | None: An associated race if it exists.

        Returns: tuple[Race, bool]:
            Race: The saved (or not) race.
            RaceDigestionStatus: The status of the race after saving.
        """
        ...

    def ingest_participant(
        self,
        race: Race,
        participant: RSParticipant,
        **kwargs,
    ) -> tuple[Participant, Status]:
        """
        Converts the fetched RSParticipant into a database Participant trying to retrieve valid data from the database.

        Args:
            race Race: The Race to witch the participant belongs.
            participant: RSParticipant: The participant to ingest.

        Returns: tuple[Participant, bool]:
            Participant: The new ingested participant.
            Status: The status of the participant after ingestion.
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

    def merge_participants(
        self,
        participant: Participant,
        db_participant: Participant,
        status: Status,
    ) -> tuple[Participant, Status]:
        """
        Merge two participants into one.

        Args:
            participant Participant: The newly ingested Participant.
            db_participant Participant: An existing database participant.
            status Status: The status of the participant.

        Returns: tuple[Participant, bool]:
            Participant: The merged participant result.
            Status: The status of participant after the merge.
        """
        ...

    def save_participant(
        self,
        participant: Participant,
        race_status: Status,
        participant_status: Status,
        is_disqualified: bool = False,
        **kwargs,
    ) -> tuple[Participant, Status]:
        """
        Save a new participant into the database.

        Args:
            participant Participant: The participant we want to save.
            race_status Status: The status of the participant race.
            participant_status Status: The status of the participant.
            is_disqualified bool: Whether the participant was disqualified or not.

        Returns: tuple[Participant, bool]:
            Participant: The saved (or not) participant.
            Status: The status of the participant after saving.
        """
        ...

    def _get_datasource(self, race: Race, ref_id: str) -> dict | None: ...

    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict: ...

    def _retrieve_race(self, race_id: str) -> Generator[RSRace, Any, Any]: ...
