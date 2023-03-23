#!/bin/bash

set -o errexit
set -o nounset

echo "### Remove old images"
rm r4l-service
rm r4l-web

echo "### Download images"
wget https://github.com/iagocanalejas/r4l/releases/latest/download/r4l-service
wget https://github.com/iagocanalejas/r4l/releases/latest/download/r4l-web

echo "### Shutdown old version"
docker-compose down

echo "### Load new docker images"
docker load -i r4l-service
docker load -i r4l-web

echo "### Wait for user input (in case some manual action needs to be done)"
read -n 1 -p "Press any key to continue:" _

echo "### Start new version"
docker-compose up -d
