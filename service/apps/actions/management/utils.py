import csv
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class ScrappedItem:
    # race data
    name: str
    t_date: date
    edition: int
    day: int
    modality: str
    league: Optional[str]
    town: Optional[str]
    organizer: Optional[str]

    # participant data
    gender: str
    category: str
    club_name: str
    lane: int
    series: int
    laps: List[str]
    distance: Optional[int]

    # normalized data
    trophy_name: str
    participant: str

    # datasource data
    race_id: str
    url: Optional[str]
    datasource: str

    # not available in all the datasource
    race_laps: Optional[int] = None
    race_lanes: Optional[int] = None
    cancelled: bool = False
    disqualified: bool = False


def save_scrapped_items(items: List[ScrappedItem], file_name: str):
    if not len(items):
        return

    file_name = file_name if '.csv' in file_name else f'{file_name}.csv'
    with open(file_name, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(items[0].__dict__.keys())  # write headers
        for item in items:
            writer.writerow(item.__dict__.values())
