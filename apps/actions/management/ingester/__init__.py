from rscraping.clients import Client
from rscraping.data.models import Datasource

from ._ingester import Ingester as Ingester
from ._protocol import IngesterProtocol as IngesterProtocol
from .traineras import TrainerasIngester as TrainerasIngester


def build_ingester(
    client: Client | None = None,
    ignored_races: list[str] = [],
) -> IngesterProtocol:
    assert client
    if client.DATASOURCE == Datasource.TRAINERAS:
        return TrainerasIngester(client, ignored_races=ignored_races)
    return Ingester(client, ignored_races=ignored_races)
