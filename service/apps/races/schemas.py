RACE_METADATA_SCHEMA = {
    '$schema': 'http://json-schema.org/schema#',
    'name': 'RaceMetadata',
    'properties': {
        'datasource': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'race_id': {'type': 'string'},
                    'datasource_name': {'type': 'string'},
                    'values': {
                        'type': 'object',
                        'additionalProperties': {'type': 'string'}
                    }
                },
                'additionalProperties': False,
                'required': ['datasource_name', 'values'],
            }
        }
    },
    'required': ['datasource'],
}


def default_race_metadata():
    return {'datasource': []}
