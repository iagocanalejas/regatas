import logging
from datetime import datetime

from django.core.exceptions import ValidationError

from rscraping import Datasource

logger = logging.getLogger(__name__)

METADATA_SCHEMA = {
    "$schema": "http://json-schema.org/schema#",
    "name": "RaceMetadata",
    "properties": {
        "datasource": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref_id": {"type": "string"},
                    "datasource_name": {"type": "string"},
                    "values": {"type": "object", "additionalProperties": {"type": "string"}},
                    "date": {"type": "string"},
                },
                "additionalProperties": False,
                # "required": ["ref_id", "datasource_name", "values", "date"],
                "required": ["ref_id", "datasource_name", "values"],  # TODO: swap this when verification ends
            },
        }
    },
    "required": ["datasource"],
}


def default_metadata():
    return {"datasource": []}


class MetadataBuilder:
    _metadata: dict

    def __init__(self):
        self._metadata = {"values": {}, "date": datetime.now().date().isoformat()}

    def ref_id(self, value: str | int) -> "MetadataBuilder":
        self._metadata["ref_id"] = str(value)
        return self

    def datasource_name(self, datasource: Datasource) -> "MetadataBuilder":
        self._metadata["datasource_name"] = datasource.value
        return self

    def values(self, key: str, value: str) -> "MetadataBuilder":
        if key in self._metadata["values"]:
            logger.warning(f'replacing {key=}:{self._metadata["values"][key]} with {value=}')
        self._metadata["values"][key] = value
        return self

    def build(self) -> dict:
        if "values" not in self._metadata:
            raise ValidationError({"values", 'required object "values" in metadata'})
        if "datasource_name" not in self._metadata:
            raise ValidationError({"datasource_name", 'required object "datasource_name" in metadata'})
        return self._metadata
