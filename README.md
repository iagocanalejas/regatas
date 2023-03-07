# Commands
## Validate
Validate a CSV file to check if it can be imported.
```sh
python manage.py validate <path>
```

#### File Columns
    name: str                       || #Race.race_name
    t_date: date                    || #Race.date, used for search (YYYY-MM-DD)
    edition: int                    || #Race.trophy_edition | #Race.flag_edition
    day: int                        || #Race.day
    modality: str                   || #Race.modality ('TRAINERA' | 'TRAINERILLA' | 'BATEL')
    league: Optional[str]           || #League.name used for search
    town: Optional[str]             || #Race.town
    organizer: Optional[str]        || #Entity.name, club organizing the event
    cancelled: Optional[bool]       || #Race.cancelled

    gender: str                     || #League.gender, if 'league' is set, #Participant.gender otherwise ('FEMALE' | 'MALE' | 'MIX').
    category: str                   || #Particpant.category ('ABSOLUT' | 'VETERAN' | 'SCHOOL').
    club_name: str                  || #Participant.club_name.
    lane: int                       || #Participant.lane
    series: int                     || #Participant.series
    laps: List[str]                 || #Participant.laps (HH:mm:ss.xxx)
    distance: int                   || #Participant.distance
    disqualified: Optional[bool]    || #Penalty.disqualified

    trophy_name: Optional[str]      || Used to search the #Trophy or #Flag, will be filled with 'name' if not provided.
    participant: Optional[str]      || #Entity[type=CLUB].name, will be filled with 'club_name' if not provided.
    race_laps: Optional[int]        || Number of laps for the #Race.laps
    race_lanes: Optional[int]       || Number of lanes for the #Race.lanes

    race_id: str                    || The ID of the race in the datasource
    url: Optional[str]              || Datasource URL where the race was found
    datasource: str                 || Datasource where the race was found


## Importfile
Import a CSV file into the database.
```sh
python manage.py importfile <path> <options>
    # --no-input: Avoids user prompts.
    # --only-validate: Does a file validation (same as validate).
```

## Scrape ACT
Scrapes the https://www.euskolabelliga.com and https://www.euskotrenliga.com pages searching for ACT races.
```sh
python manage.py scrapeact <options>
    # --female: Search in the 'euskotren' page.
    # --year=<year>: Search races for the given year.
    # --all: Search all races since 2003 (2009 if --female is set).
```

## Scrape ARC
Scrapes the https://www.liga-arc.com and http://www.ligaete.com pages searching for ARC and ETE races.
```sh
python manage.py scrapearc <options>
    # --female: Search in the 'ETE' page.
    # --year=<year>: Search races for the given year.
    # --all: Search all races since 2006 (2018 if --female is set).
```

## Scrape LGT
Scrapes the https://www.ligalgt.com/ page searching for LGT races.
```sh
python manage.py scrapelgt <options>
    # --race_id: Race id to search.
    # --all: Search all the races.
```

## Parse Image
Scrapes the https://www.ligalgt.com/ page searching for LGT races.
```sh
python manage.py parseimage <path> <options>
    # --datasource=<source>: Datasource to be used in the processing.
    #     - inforemo
    # --plot: Plot the image processing and dataframes done.
```

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

# Development
## Update .env.gpt
```sh
# Password is on the Bitwarden
gpg --symmetric --cipher-algo AES256 .env
```

## Backup Database to YAML
```sh
python manage.py dumpdata > <name>.yaml --format yaml --exclude admin.logentry --exclude auth --exclude sessions --exclude contenttypes
```

# Docker

## Docker (manual) DEV environment
```sh
docker-compose up -f docker-compose.dev.yml
```