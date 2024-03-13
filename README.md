# Commands

## Find race

Retrieve and process race data from a web datasource, JSON file and spreadsheet.

```sh
python manage.py findrace input_source [race_ids] \
	[-f, --female] \
	[--day DAY] \
	[-o, --output OUTPUT]

#   Arguments:
#       input_source:
#           The name of the Datasource or path to import data from.
#
#       race_ids (optional)
#           Races to find and ingest.
#           NOTE: This argument is mandatory for Datasource and not supported for local files.
#
#   Options:
#       -d, --day DAY
#           Day of the race.
#           NOTE: This option is only supported for the TRAINERAS datasource.
#
#       -f, --female:
#           Import data for female races.
#
#       -o, --output:
#           Outputs the race data to the given folder path in JSON format.
```

## Scrape races

Retrieve and process race data from a web datasource, JSON file and spreadsheet.

```sh
python manage.py scraperaces input_source [year] \
	[-f, --female] \
	[-c, --category CATEGORY] \
	[--sheet-id SHEET_ID] \
	[--sheet-name SHEET_NAME] \
	[--file-path FILE_PATH] \
	[-i, --ignore ID [ID ...]] \
	[-o, --output OUTPUT]

#   Arguments:
#       input_source:
#           The name of the Datasource or path to import data from.
#
#       year:
#           The year for which race data should be imported.
#           NOTE: This argument is mandatory for Datasource and not supported for local files.
#
#   Options:
#       -f, --female:
#           Import data for female races.
#
#       -c, --category:
#           Import data for the given category (ABSOLUT | VETERAN | SCHOOL).
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
```

## Database commands

Command utilities for cleaning the database.

```sh
python manage.py database <command>
    # COMMANDS:
        # checkeditions: search for races with non consecutive editions.
        # fillorganizers: prompts the user to set the organizer of empty races.
        # checklaps: search for races with different laps.
        # checklanes: search for races with different lanes.
		# checkgenders: search for different gender in the participants of races not marked as 'ALL'.
    # -m, --model [trophy|flag]: Model to target for the command.
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
