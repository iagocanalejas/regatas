#!/bin/sh

set -o errexit
set -o nounset

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

# Run celery
rm -f './celerybeat.pid'
celery -A config.celery.app worker -l INFO --detach
celery -A config.celery.app beat -l INFO --detach

worker_ready() {
  celery -A config.celery.app inspect ping
}
until worker_ready; do
  echo >&2 'Celery workers not available'
  sleep 1
done
echo >&2 'Celery workers is available'

celery -A config.celery.app --broker="${CELERY_BROKER}" flower --detach

# This will exec the CMD from your Dockerfile, i.e. "npm start"
exec "$@"
