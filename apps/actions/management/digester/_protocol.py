from enum import Enum, auto
from typing import Protocol

from apps.participants.models import Participant, Penalty
from apps.races.models import Flag, Race, Trophy
from rscraping.clients import ClientProtocol
from rscraping.data.models import Datasource
from rscraping.data.models import Participant as RSParticipant
from rscraping.data.models import Penalty as RSPenalty
from rscraping.data.models import Race as RSRace


class DigesterProtocol(Protocol):
    client: ClientProtocol

    class Status(Enum):
        IGNORE = auto()
        EXISTING = auto()

        NEW = auto()
        MERGED = auto()

        CREATED = auto()
        UPDATED = auto()

        def next(self) -> "DigesterProtocol.Status":
            if self == self.NEW:
                return self.CREATED
            if self == self.MERGED:
                return self.UPDATED
            return self

        def is_saved(self) -> bool:
            return self in [self.CREATED, self.UPDATED]

    def ingest(
        self,
        race: RSRace,
        hint: tuple[Flag, Trophy] | None = None,
        **kwargs,
    ) -> tuple[Race, Race | None, Status]:
        """
        Converts the fetched RSRace into a database Race trying to retrieve valid data from the database.

        Args:
            race: RSRace: The race to ingest.
            hint: tuple[Flag, Trophy]: The hint to find the race in the database.

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
        can_be_branch: bool,
        **kwargs,
    ) -> tuple[Participant, Status]:
        """
        Converts the fetched RSParticipant into a database Participant trying to retrieve valid data from the database.

        Args:
            race Race: The Race to witch the participant belongs.
            participant: RSParticipant: The participant to ingest.
            can_be_branch: bool: Whether the participant can be a branch or not.

        Returns: tuple[Participant, bool]:
            Participant: The new ingested participant.
            Status: The status of the participant after ingestion.
        """
        ...

    def get_participant_fields_to_update(self, participant: Participant, db_participant: Participant) -> list[str]:
        """
        Check if two participants should be merged and what fields to merge.

        Args:
            participant Participant: The newly ingested Participant.
            db_participant Participant: An existing database participant.

        Returns: list[str]: The fields to update.
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

    def save_penalty(self, participant: Participant, penalty: RSPenalty, note: str | None, **kwargs) -> Penalty:
        """
        Save a new penalty into the database, or update existing one if it matches.

        Args:
            participant Participant: The participant to save the penalty.
            penalty RSPenalty: The penalty to save.
            note str | None: The note from where the penalty was created.

        Returns: Penalty: The saved penalty.
        """
        ...

    def _build_metadata(self, race: RSRace, datasource: Datasource) -> dict: ...

    def _build_participant_metadata(self, participant: RSParticipant, datasource: Datasource) -> dict: ...
