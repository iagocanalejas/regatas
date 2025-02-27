from rscraping.clients import Client
from rscraping.data.constants import GENDER_MALE
from rscraping.data.models import Datasource


def build_client(
    source: Datasource | None,
    gender: str = GENDER_MALE,
    category: str | None = None,
) -> Client | None:
    return Client(source=source, gender=gender, category=category) if source else None
