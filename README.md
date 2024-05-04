# Commands

## Scrape Races

Retrieve and process race data from a web datasource, JSON file or spreadsheet.

```sh
python manage.py scrape input_source [RACE_ID [RACE_ID ...]] \
	[--year YEAR] \
	[--start-year YEAR] \
	[-g, --gender] \
	[-c, --category CATEGORY] \
	[-d, --day DAY] \
	[--sheet-id SHEET_ID] \
	[--sheet-name SHEET_NAME] \
	[--file-path FILE_PATH] \
	[-i, --ignore ID [ID ...]] \
	[-o, --output OUTPUT]

# positional arguments:
#   input_source          name of the Datasource or path to import data from.
#   race_ids              race IDs to find in the source and ingest.
#
# options:
#   --club CLUB
#                         club for which races should be imported.
#   --year YEAR
#                         year for which races should be imported, 'all' to import from the source beginnig.
#   --start-year START_YEAR
#                         year for which we should start processing years. Only used with year='all'.
#   --sheet-id SHEET_ID
#                         google-sheet ID used for TABULAR datasource.
#   --sheet-name SHEET_NAME
#                         google-sheet name used for TABULAR datasource.
#   --file-path FILE_PATH
#                         sheet file path used for TABULAR datasource.
#   -d DAY, --day DAY
#                         day of the race for multiday races.
#   -g, --gender
#                         races gender.
#   -c CATEGORY, --category CATEGORY
#                         one of (ABSOLUT | VETERAN | SCHOOL).
#   -i [IGNORE ...], --ignore [IGNORE ...]
#                         race IDs to ignore during ingestion.
#   -o OUTPUT, --output OUTPUT
#                         Outputs the race data to the given folder path in JSON format.
```

## Find Races

Retrieve races from the database searching by race ID or datasource and ref_id.

```sh
python manage.py find datasource_or_race [REF_ID]

# positional arguments:
#   datasource_or_race    name of the Datasource or race ID in the database.
#   ref_id                reference ID for the given Datasource.
```

## Verify Races

Retrieve races from the database and verifies it's datasources ara correct.

```sh
python manage.py validate datasource [year]

# positional arguments:
#   datasource            The name of the Datasource that will be validated
#   year                  The year for which race data should be verified.
```

## Plot Data

Use boxplot graphs to visualize each year speeds.

```sh
python manage.py plot [club]

# positional arguments:
#   club                  club ID to filter participants.
#
# options:
#   -g, --gender          races gender.
#   --leagues-only        only races from a league.
#   --branch-teams        filter only branch teams.
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
