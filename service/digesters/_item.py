from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class ScrappedItem:
    league: Optional[str]
    name: str
    gender: Optional[str]
    edition: int
    day: int
    t_date: date
    club_name: str
    lane: int
    series: int
    laps: List[str]

    # normalized data
    trophy_name: str
    participant: str

    # datasource data
    race_id: str
    url: Optional[str]
    datasource: str

    # not available in all the datasource
    town: Optional[str]
    organizer: Optional[str]
    race_laps: Optional[int] = None
    race_lanes: Optional[int] = None
    cancelled: bool = False
    disqualified: bool = False
