import os.path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from utils import build_client

from apps.actions.management.ingester import TrainerasIngester, build_ingester
from rscraping.data.models import Datasource, dataclass


@dataclass
class Response:
    content: bytes


class TrainerasIngestionTest(TestCase):
    def setUp(self):
        client = build_client(Datasource.TRAINERAS)
        self.ingester = build_ingester(client)
        assert isinstance(self.ingester, TrainerasIngester)

    @patch("requests.get")
    def test_ingest(self, mock_get):
        with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", "multirace_2506.html")) as f:
            mock_get.return_value = Response(content=f.read().encode("utf-8"))

        races = list(self.ingester._retrieve_race("2506"))
        self.assertEqual(len(races), 3)
