# Commands

## Scrape Races

Retrieve and process race data from a web datasource, JSON file or spreadsheet.

```sh
python manage.py scrape datasource [RACE_ID [RACE_ID ...]] \
	[-c, --club CLUB] \
	[-e, --entity ENTITY] \
	[-f, --flag FLAG] \
	[-y, --year YEAR] \
	[-sy, --start-year YEAR] \
	[-t, --table TABLE] \
	[-g, --gender] \
	[-ca, --category CATEGORY] \
	[-i, --ignore ID [ID ...]] \
	[-w, --last-weekend] \
	[--force-gender] \
	[--force-category] \
	[--save-old] \
	[-o, --output OUTPUT]

# positional arguments:
#   datasource            name of the Datasource to import data from.
#   race_ids              raceIDs to find in the source and ingest.
#
# options:
#   -c CLUB, --club CLUB
#                         clubID for which races should be imported.
#   -e ENTITY, --entity ENTITY
#                         entityID for which races should be imported.
#   -f FLAG, --flag FLAG
#                         flagID for which races should be imported.
#   -y YEAR, --year YEAR  year for which races should be imported, 'all' to import from the source beginnig.
#   -sy START_YEAR, --start-year START_YEAR
#                         year for which we should start processing years. Only used with year='all'.
#   -t TABLE, --table TABLE
#                         table of the race for multipage races.
#   -g GENDER, --gender GENDER
#                         gender filter.
#   -ca CATEGORY, --category CATEGORY
#                         category filter.
#   -i [IGNORE ...], --ignore [IGNORE ...]
#                         raceIDs to ignore during ingestion.
#   -w, --last-weekend
#                         fetches the races for the last weekend.
#   --force-gender
#                         forces the gender to match.
#   --force-category
#                         forces the category to match.
#   --save-old
#                         automatically saves the races before 2003 without asking.
#   -o OUTPUT, --output OUTPUT
#                         Outputs the race data to the given folder path in JSON format.
```

#### Examples

```sh
# Scrape last weekend races from the LGT datasource forcing the gender and category match in the DB.
python manage.py scrape lgt -w --force-gender --force-category
```

## Recheck Races

Recheck the already full imported flags to find new races.

```sh
python manage.py recheck datasource \
	[-f, --flag FLAG] \
	[--check-participants] \
	[--only-new] \
	[--force-gender] \
	[--force-category]

# positional arguments:
#   datasource            name of the Datasource.
#
# options:
#   -f FLAG, --flag FLAG
#                         flagID for which races should be imported.
#   --check-participants
#                         checks if the number of participants matches.
#   --only-new
#                         scrape only newer races than the last one in database.
#   --force-gender
#                         forces the gender to match.
#   --force-category
#                         forces the category to match.
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

## Create a fixture to use in tests

```sh
# Comment custom soft-deletes in the models.
python manage.py dumpdata races.race --pks=<PK> > race.json
python manage.py dumpdata participants.participant --pks=<PK1,PK2,...> > participants.json
jq -s '.[0] + .[1]' race.json participants.json > combined.json
jq -s '.[0] + .[1]' fixtures/frozen-db.json combined.json > copy.json
mv copy.json fixtures/frozen-db.json
rm race.json participants.json combined.json
```
