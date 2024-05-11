from rscraping.clients import Client, TabularClientConfig, TabularDataClient
from rscraping.data.constants import GENDER_MALE
from rscraping.data.models import Datasource


def build_client(
    source: Datasource | None,
    gender: str = GENDER_MALE,
    tabular_config: TabularClientConfig | None = None,
    category: str | None = None,
) -> Client | None:
    if not source:
        return None
    if source == Datasource.TABULAR:
        return TabularDataClient(source=source, config=tabular_config, gender=gender)
    return Client(source=source, gender=gender, category=category)
