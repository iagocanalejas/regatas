from rscraping.clients import Client
from rscraping.data.constants import GENDER_FEMALE, GENDER_MALE
from rscraping.data.models import Datasource


def build_client(
    source: Datasource | None,
    gender: str | None = None,
    category: str | None = None,
) -> Client:
    assert source is not None, "invalid source"
    if gender is None:
        gender = GENDER_FEMALE if source in {Datasource.ETE} else GENDER_MALE
    return Client(source=source, gender=gender, category=category)
