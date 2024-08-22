# Commands

## Scrape Races

Retrieve and process race data from a web datasource, JSON file or spreadsheet.

```sh
python manage.py scrape input_source [RACE_ID [RACE_ID ...]] \
	[-c, --club CLUB] \
	[-e, --entity ENTITY] \
	[-f, --flag FLAG] \
	[-y, --year YEAR] \
	[-sy, --start-year YEAR] \
	[-t, --table TABLE] \
	[-g, --gender] \
	[-ca, --category CATEGORY] \
	[--sheet-id SHEET_ID] \
	[--sheet-name SHEET_NAME] \
	[--file-path FILE_PATH] \
	[-i, --ignore ID [ID ...]] \
	[-w, --last-weekend] \
	[--force-gender] \
	[--force-category] \
	[-o, --output OUTPUT]

# positional arguments:
#   input_source          name of the Datasource or path to import data from.
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
#   --sheet-id SHEET_ID
#                         google-sheet ID used for TABULAR datasource.
#   --sheet-name SHEET_NAME
#                         google-sheet name used for TABULAR datasource.
#   --file-path FILE_PATH
#                         sheet file path used for TABULAR datasource.
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
#   -o OUTPUT, --output OUTPUT
#                         Outputs the race data to the given folder path in JSON format.
```

#### Examples

```sh
# Scrape last weekend races from the LGT datasource forcing the gender and category match in the DB.
python manage.py scrape lgt -w --force-gender --force-category
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
python manage.py plot \
	[-c, --club CLUB_ID] \
	[-l, --league LEAGUE_ID] \
	[-t, --type PLOT_TYPE] \
	[-i, --index INDEX] \
	[-g, --gender GENDER] \
	[-ca, --category CATEGORY] \
	[-y, --years YEARS] \
	[-n, --normalize] \
	[--leagues-only] \
	[--branch-teams] \
	[-o, --output FILE]

# options:
#   -t TYPE, --type TYPE
#                         plot type ['boxplot', 'line', 'nth'].
#   -i INDEX, --index INDEX
#                         position to plot the speeds in 'nth' charts.
#   -c CLUB, --club CLUB
#                         club ID for which to load the data.
#   -l LEAGUE, --league LEAGUE
#                         league ID for which to load the data.
#   -g GENDER, --gender GENDER
#                         gender filter.
#   -ca CATEGORY, --category CATEGORY
#                         category filter.
#   -y [YEARS ...], --years [YEARS ...]
#                         years to include in the data.
#   --leagues-only
#                         only races from a league.
#   --branch-teams
#                         filter only branch teams.
#   -n, --normalize
#                         exclude outliers based on the speeds' standard deviation.
#   -o OUTPUT, --output OUTPUT
#                         saves the output plot.
```

#### Examples

```sh
# Plot the winner speed of each race for the league 5 in 2015, 2016, 2017, and 2018.
# The plot will be saved in the Downloads folder with the name test.png.
python manage.py plot --league 5 -t nth -i 1 -y 2015 2016 2017 2018 -o ~/Downloads/p.png
```

```sh
# Plot the normalized leaghe speeds of the Puebla team for all the years.
python manage.py plot 25 --leagues-only -n -o ~/Downloads/p.png
```

```sh
# Plot the speeds of the Puebla team for the league 5 in 2021, 2022, and 2023.
python manage.py plot 25 --league 5 -t line -y 2021 2022 2023 -o ~/Downloads/p.png
```

```sh
# Plot all leagues AVG speeds per year.
# The plot will be saved in the Downloads folder with a generated name.
parallel -j 11 python manage.py plot --league {} -o ~/Downloads/l{}.png ::: $(seq 1 11)
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
