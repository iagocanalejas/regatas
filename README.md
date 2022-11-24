## Environment variables
Defaults if not replaced in `.env` file.
```
DEBUG=False
SECRET_KEY=what-a-fake-secret-key-lol

## DATABASE
DATABASE_HOST=localhost
DATABASE_NAME=rowing
DATABASE_USERNAME=service
DATABASE_PASSWORD=service
DATABASE_PORT=5432

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
python manage.py dumpdata > db_cleaning.yaml --format yaml --exclude admin.logentry --exclude auth --exclude sessions --exclude contenttypes
```

# Docker
## Docker login
```sh
# login to Docker registry
docker login -u <your_username> -p <your_personal_access_token>
```

## Docker (manual) DEV environment
```sh
docker build -t r4l/service .

docker build
	--build-arg prod=false 
	--build-arg nginx=nginx.dev.conf
	-t r4l/web .

docker run
	-p 5432:5432
	-v <PATH_TO_LOCAL_SHARED>/shared:/srv/www/r4l/shared
	--env DOCKER=True
	--env DATABASE_HOST=host.docker.internal
	--name r4l-service
	--env-file .env
	--net r4l
	r4l/service 

docker run
	-p 8080:8080
	-v <PATH_TO_LOCAL_SHARED>/shared:/srv/www/r4l/shared
	--name r4l-web
	--net r4l
	r4l/web 
```

# Notes:
```
// race with disqualified participant = 33
// race with missing laps = 848
// races without participation = [686, 752, 756, 759, 758, 764, 766, 772, 774, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 790, 791, 793, 828]
```