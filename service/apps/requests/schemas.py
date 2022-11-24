KEY_VALUE_SCHEMA = {
    "$schema": "http://json-schema.org/schema#",
    "name": "KeyValue",
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
