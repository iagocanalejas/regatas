RACE_METADATA_SCHEMA = {
    "$schema": "http://json-schema.org/schema#",
    "name": "RaceMetadata",
    "properties": {
        "datasource": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "race_id": {
                        "type": "string",
                    },
                    "datasource_name": {
                        "type": "string",
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {
                                    "type": "string",
                                },
                                "value": {
                                    "type": "string",
                                }
                            },
                            "required": ["key", "value"],
                        }
                    }
                },
                "required": ["race_id", "datasource_name"],
            }
        }
    },
    "required": ["datasource"],
}


def default_race_metadata():
    return {"datasource": []}
