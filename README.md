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
## Docker login
```sh
# login to Docker registry
docker login -u <your_username> -p <your_personal_access_token>
```

## Docker (manual) DEV environment
```sh
docker-compose up -f docker-compose.dev.yml
```

# Notes:
```
// race with disqualified participant = 33
// race with missing laps = 848
// races without participation = [686, 752, 756, 759, 758, 764, 766, 772, 774, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 790, 791, 793, 828]
```