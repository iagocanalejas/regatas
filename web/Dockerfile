### Stage 1: build ###
FROM node:lts as builder

ARG build_command='npm run build:prod'

# Copy all files not in .dockerignore and set workdir
ADD . /app
WORKDIR /app

# Install app dependencies.
RUN npm install

# Disable node cache
RUN npm run disable:cache

# Build app
RUN eval $build_command
RUN rm -rf /app/dist/web/assets/scss

#===================================================#

### Stage 2: delivery ###
FROM nginx

ARG nginx=nginx.prod.conf

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*
RUN mkdir -p /srv/www/r4l/web

# Copy output directory from builder to nginx image.
COPY --from=builder /app/dist/web /srv/www/r4l/web

# Copy nginx configuration file.
COPY ./$nginx /srv/www/r4l/web/default.conf

# Copy entrypoint and give permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]
