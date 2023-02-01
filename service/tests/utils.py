import os

import responses
from django.conf import settings


def add_html_response(url: str, file: str, method=responses.GET):
    with open(os.path.join(settings.BASE_DIR, 'fixtures', 'html', file)) as file:
        responses.add(method, url, body=file.read(), status=200)
