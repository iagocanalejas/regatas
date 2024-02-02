# Commands

## Find race

Retrieve and process race data from a web datasource or file.

```sh
python manage.py findrace datasource_or_file [race_ids] [--female] [--day DAY] [--use-db]
# Arguments:
#   datasource_or_file   Datasource or file from where to retrieve the race data.
#   race_ids (optional)  List of races to find (required if the datasource_or_file is a file).
#
# Options:
#   --day DAY            Day of the race (used in multi-race pages).
#   --female             Specify if the race is female.
#   -o, --output OUTPUT  Output path to save the scrapped data.
#   --use-db             Use the database to retrieve race data.
#	--ignore-entities    Ignore the entities that doesn't exist in the database.
```

## Scrape races

Imports data from a web datasource.

```sh
python manage.py scraperaces datasource_or_folder [year] [--female] [--category CATEGORY] [--ignore ID [ID ...]] [-o OUTPUT]
# Arguments:
#   datasource_or_folder    The name of the web datasource or path to a folder to import data from.
#   year (optional)         The year for which races data should be imported.
#
# Options:
#   -f, --female                If specified, import data for female races.
#   -c, --category              If specified, import data for the given category (ABSOLUT | VETERAN | SCHOOL).
#   --ignore ID [ID ...]        List of race IDs to ignore during import.
#   -o, --output OUTPUT         Output path to save the scrapped data.
```

## Import _MY_ excel data

Imports data from my excel datasource.

```sh
python manage.py importfile <path> <entity_id>
    # --female: Search in the female version of the pages.
```

## Database commands

Command utilities for cleaning the database.

```sh
python manage.py database <command>
    # COMMANDS:
        # missingeditions: search for races with non consecutive editions.
        # fillorganizers: prompts the user to set the organizer of empty races.
    # -m, --model [trophy|flag]: Model to target for the command.
```

# Bump version

Syncs the versions of all the subprojects choosing the on in the root's `package.json`.

```sh
python bump.py
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
