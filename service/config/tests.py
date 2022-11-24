DEBUG = False
DOCKER = False

ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = False

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
