from rscraping.clients import Client

from ._digester import Digester as Digester
from ._protocol import DigesterProtocol as DigesterProtocol


def build_digester(
    client: Client | None = None,
    force_gender: bool = False,
    force_category: bool = False,
    save_old: bool = False,
) -> DigesterProtocol:
    assert client
    return Digester(client, force_gender=force_gender, force_category=force_category, save_old=save_old)
