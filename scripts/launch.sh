#!/bin/bash

DOMAIN=tiempostraineras.com
CERTBOT_PATH="./docker/certbot"

if ! [ -x "$(command -v docker)" ]; then
  echo "### Installing docker, machine will reboot"
  sudo amazon-linux-extras install -y docker
  sudo service docker start
  sudo usermod -a -G docker ec2-user
  sudo chkconfig docker on
  sudo reboot
fi

echo "### Load docker images"
docker load -i r4l-service
docker load -i r4l-web

if ! [ -x "$(command -v docker-compose)" ]; then
  echo "### Install docker-compose"
  sudo curl -L https://github.com/docker/compose/releases/download/latest/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  docker-compose version
fi

if [ -d "$CERTBOT_PATH" ]; then
  read -r -p "Existing data found for $DOMAIN. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

if [ ! -e "$CERTBOT_PATH/conf/options-ssl-nginx.conf" ] || [ ! -e "$CERTBOT_PATH/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$CERTBOT_PATH/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf >"$CERTBOT_PATH/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem >"$CERTBOT_PATH/conf/ssl-dhparams.pem"
  echo
fi

echo "### Creating dummy certificate for $DOMAIN ..."
path="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "$CERTBOT_PATH/conf/live/$DOMAIN"
docker-compose run --rm --entrypoint "openssl req -x509 -nodes -newkey rsa:1024 -days 1 -keyout '$path/privkey.pem' -out '$path/fullchain.pem' -subj '/CN=localhost'" certbot
echo

echo "### Starting nginx ..."
docker-compose up --force-recreate -d web
echo

echo "### Deleting dummy certificate for $DOMAIN ..."
docker-compose run --rm --entrypoint "rm -Rf /etc/letsencrypt/live/$DOMAIN && rm -Rf /etc/letsencrypt/archive/$DOMAIN && rm -Rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot
echo

echo "### Requesting Let's Encrypt certificate for $DOMAIN ..."
docker-compose run --rm --entrypoint "certbot certonly --webroot -w /var/www/certbot --email andiag.dev@gmail.com -d $DOMAIN -d www.$DOMAIN --rsa-key-size 4096 --agree-tos --no-eff-email --force-renewal" certbot
echo

echo "### Reloading nginx ..."
docker-compose exec web nginx -s reload

echo "### Launching R4L"
docker-compose up -d