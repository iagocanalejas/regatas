import os

from rscraping.clients import Client, TabularClientConfig, TabularDataClient
from rscraping.data.models import Datasource

from ._ingestor import Ingestor as Ingestor
from ._protocol import IngestorProtocol as IngestorProtocol
from .folder import FolderIngestor as FolderIngestor
from .tabular import TabularIngestor as TabularIngestor
from .traineras import TrainerasIngestor as TrainerasIngestor


def build_ingestor(
    source: Datasource | str,
    is_female: bool = False,
    tabular_config: TabularClientConfig | None = None,
    category: str | None = None,
    ignored_races: list[str] = [],
) -> IngestorProtocol:
    if os.path.isdir(source) or os.path.isfile(source):
        return FolderIngestor(source)

    assert isinstance(source, Datasource)
    if source == Datasource.TABULAR:
        client = TabularDataClient(source=source, config=tabular_config, is_female=is_female)
        assert isinstance(client, TabularDataClient)
        return TabularIngestor(client, ignored_races=ignored_races)
    if source == Datasource.TRAINERAS:
        return TrainerasIngestor(
            Client(source=source, is_female=is_female, category=category), ignored_races=ignored_races
        )

    return Ingestor(Client(source=source, is_female=is_female), ignored_races=ignored_races)
