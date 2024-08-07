# Commands

## Scrape Races

Retrieve and process race data from a web datasource, JSON file or spreadsheet.

```sh
python manage.py scrape input_source [RACE_ID [RACE_ID ...]] \
	[--club CLUB] \
	[--entity ENTITY] \
	[--flag FLAG] \
	[--year YEAR] \
	[--start-year YEAR] \
	[-c, --category CATEGORY] \
	[-d, --day DAY] \
	[-g, --gender] \
	[--sheet-id SHEET_ID] \
	[--sheet-name SHEET_NAME] \
	[--file-path FILE_PATH] \
	[-w, --last-weekend] \
	[--force-gender] \
	[--force-category] \
	[-i, --ignore ID [ID ...]] \
	[-o, --output OUTPUT]

# positional arguments:
#   input_source          name of the Datasource or path to import data from.
#   race_ids              race IDs to find in the source and ingest.
#
# options:
#   --club CLUB
#                         datasource club ID for which races should be imported.
#   --entity ENTITY
#                         database entity ID for which races should be imported.
#   --flag FLAG
#                         datasource flag ID for which races should be imported.
#   --year YEAR
#                         year for which races should be imported, 'all' to import from the source beginnig.
#   --start-year START_YEAR
#                         year for which we should start processing years. Only used with year='all'.
#   -c CATEGORY, --category CATEGORY
#                         one of (ABSOLUT | VETERAN | SCHOOL).
#   -d DAY, --day DAY
#                         day of the race for multiday races.
#   -g GENDER, --gender GENDER
#                         races gender.
#   --sheet-id SHEET_ID
#                         google-sheet ID used for TABULAR datasource.
#   --sheet-name SHEET_NAME
#                         google-sheet name used for TABULAR datasource.
#   --file-path FILE_PATH
#                         sheet file path used for TABULAR datasource.
#   -w, --last-weekend
#                         ingest only the last weekend races.
#   --force-gender
#                         forces the gender to match.
#   --force-category
#                         forces the category to match.
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

## Plot Data

Use boxplot graphs to visualize each year speeds.

```sh
python manage.py plot [club]

# positional arguments:
#   club                  club ID to filter participants.
#
# options:
#   --league              league ID to filter participants.
#   -g, --gender          races gender.
#   --leagues-only        only races from a league.
#   --branch-teams        filter only branch teams.
#   -n, --normalize       exclude outliers based on the speeds' standard deviation.
```

```sh
# Plot all leagues
parallel -j 11 python manage.py plot --league {} -o out/l{}.png ::: $(seq 1 11)
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
