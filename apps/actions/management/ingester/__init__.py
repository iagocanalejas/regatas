import os

from rscraping.clients import Client, TabularDataClient
from rscraping.data.models import Datasource

from ._ingester import Ingester as Ingester
from ._protocol import IngesterProtocol as IngesterProtocol
from .folder import FolderIngester as FolderIngester
from .tabular import TabularIngester as TabularIngester
from .traineras import TrainerasIngester as TrainerasIngester


def build_ingester(
    client: Client | None = None,
    path: str | None = None,
    ignored_races: list[str] = [],
) -> IngesterProtocol:
    if path and (os.path.isdir(path) or os.path.isfile(path)):
        return FolderIngester(path)

    assert client
    if client.DATASOURCE == Datasource.TABULAR:
        assert isinstance(client, TabularDataClient)
        return TabularIngester(client, ignored_races=ignored_races)
    if client.DATASOURCE == Datasource.TRAINERAS:
        return TrainerasIngester(client, ignored_races=ignored_races)
    return Ingester(client, ignored_races=ignored_races)
