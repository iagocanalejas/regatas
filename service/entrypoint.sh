#!/bin/sh
echo "### Starting service as $(whoami)"

LOG_PATH=/srv/www/r4l/logs

# Prepare log files
mkdir -p ${LOG_PATH}
touch -a ${LOG_PATH}/gunicorn.log
touch -a ${LOG_PATH}/gunicorn-access.log
touch -a ${LOG_PATH}/django-debug.log
touch -a ${LOG_PATH}/django-errors.log

# Activate the virtual environment
export DJANGO_WSGI_MODULE=config.wsgi
export LOGS_PATH=${LOG_PATH}
export DOCKER=True

# Collect django statics
python manage.py collectstatic --noinput

# Move to used folder
mkdir -p /srv/www/r4l/shared/static
cp -r ./static/* /srv/www/r4l/shared/static

# This will exec the CMD from your Dockerfile, i.e. "npm start"
exec "$@"
