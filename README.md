# Commands

## Scrape Races

Retrieve and process race data from a web datasource, JSON file or spreadsheet.

```sh
python manage.py scrape input_source [RACE_ID [RACE_ID ...]] \
	[--year YEAR] \
	[-f, --female] \
	[-c, --category CATEGORY] \
	[-d, --day DAY] \
	[--sheet-id SHEET_ID] \
	[--sheet-name SHEET_NAME] \
	[--file-path FILE_PATH] \
	[-i, --ignore ID [ID ...]] \
	[-o, --output OUTPUT]

#   Arguments:
#       input_source:
#           The name of the Datasource or path to import data.
#
#       race_ids (optional)
#           Races to find and ingest.
#
#   Options:
#       --year YEAR
#           The year for which race data should be imported.
#
#       -f, --female:
#           Import data for female races.
#
#       -c, --category:
#           Import data for the given category (ABSOLUT | VETERAN | SCHOOL).
#           NOTE: This option is only supported for the TRAINERAS datasource.
#
#       -d, --day DAY
#           Day of the race.
#           NOTE: This option is only supported for the TRAINERAS datasource.
#
#       --sheet-id:
#           Google sheet ID used for TABULAR datasource.
#
#       --sheet-name:
#           Google sheet name used for TABULAR datasource.
#
#       --file-path:
#           Sheet file path used for TABULAR datasource.
#
#       -i, --ignore:
#           List of race IDs to ignore during ingestion.
#
#       -o, --output:
#           Outputs the race data to the given folder path in JSON format.
#
#   NOTE: One of 'year' | 'race_ids' is required and they are mutually exclusive.
```

## Find Races

Retrieve races from the database searching by race ID or datasource and ref_id.

```sh
python manage.py find datasource_or_race [REF_ID]

#   Arguments:
#       datasource_or_race:
#           The name of the Datasource or race ID to retrieve.
#       ref_id:
#           The reference ID to search for.
```

## Verify Races

Retrieve races from the database and verifies it's datasources ara correct.

```sh
python manage.py validatedatasource datasource [year]

#   Arguments:
#       datasource:
#           The name of the Datasource that will be validated.
#
#       year:
#           The year of the races that will be processed.
```

# Development

## Environment variables

Default `.env` file.

```
DEBUG=False
SECRET_KEY=what-a-fake-secret-key-lol

## DATABASE
DATABASE_HOST=localhost
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres

## EMAIL
EMAIL_HOST_USER=,
EMAIL_HOST_PASSWORD=,
```

## Backup Database to YAML

```sh
python manage.py dumpdata > <name>.yaml --format yaml --exclude admin.logentry --exclude auth --exclude sessions --exclude contenttypes
```
