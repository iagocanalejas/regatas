# Default image to use
FROM python:3.11.1

ENV bind ${bind:-'unix:/run/r4l/.sock'}

# Copy all files not in .dockerignore and set workdir
ADD . /app
WORKDIR /app

# Copy requirements and install dependencies
COPY config/requirements/prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint and give permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Install and start redis for Django jobs
RUN apt-get update \
    && apt-get autoremove -y

ENTRYPOINT ["/entrypoint.sh"]
CMD exec gunicorn config.wsgi:application \
    --name="R4L" \
    --bind=$bind \
    --workers=2 \
    --log-level=info \
    --log-file=/srv/www/r4l/logs/gunicorn.log \
    --access-logfile=/srv/www/r4l/logs/gunicorn-access.log \
    --daemon
