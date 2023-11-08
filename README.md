# Commands

## Find race

Finds and scrapes a specific race from a web datasource.

```sh
python manage.py findrace <datasource> <race_id>
    # --female: Search in the female version of the pages.
    # --day: For multi-day pages (like in traineras.es) tries to find the given day of a race.
    # --use-db: Uses a race found in the database instead the one parsed.
```

## Scrape races

Imports data from a web datasource.

```sh
python manage.py scraperaces <datasource> <year>
    # --female: Search in the female version of the pages.
	# --ignore: List of ignored race IDs.
    # --all: Search all races in the given datasource.
```

## Import _MY_ excel data

Imports data from my excel datasource.

```sh
python manage.py myraces <path> <entity_id>
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
