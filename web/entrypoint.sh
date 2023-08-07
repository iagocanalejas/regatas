#!/bin/sh
echo "### Starting nginx as $(whoami)"

LOG_PATH=/srv/www/r4l/logs

# Prepare log files
mkdir -p ${LOG_PATH}
touch -a ${LOG_PATH}/nginx-access.log
touch -a ${LOG_PATH}/nginx-errors.log

cp /srv/www/r4l/web/default.conf /etc/nginx/conf.d/default.conf
rm /srv/www/r4l/web/default.conf

# This will exec the CMD from your Dockerfile, i.e. "npm start"
exec "$@"
