import os

from rscraping.clients import Client, TabularDataClient
from rscraping.data.models import Datasource

from ._digester import Digester as Digester
from ._protocol import DigesterProtocol as DigesterProtocol
from .folder import FolderDigester as FolderDigester
from .tabular import TabularDigester as TabularDigester


def build_digester(
    client: Client | None = None,
    path: str | None = None,
) -> DigesterProtocol:
    if path and (os.path.isdir(path) or os.path.isfile(path)):
        return FolderDigester(path)

    assert client
    if client.DATASOURCE == Datasource.TABULAR:
        assert isinstance(client, TabularDataClient)
        return TabularDigester(client)
    return Digester(client)
