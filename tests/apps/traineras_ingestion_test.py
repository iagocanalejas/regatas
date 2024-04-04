import os.path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from apps.actions.management.ingestor import build_ingestor
from apps.actions.management.ingestor.traineras import TrainerasIngestor
from rscraping.data.models import Datasource, dataclass


@dataclass
class Response:
    content: bytes


class TrainerasIngestionTest(TestCase):
    def setUp(self):
        self.ingestor = build_ingestor(Datasource.TRAINERAS)
        assert isinstance(self.ingestor, TrainerasIngestor)

    @patch("requests.get")
    def test_ingest(self, mock_get):
        with open(os.path.join(settings.BASE_DIR, "fixtures", "ingestion", "multirace_2506.html")) as f:
            mock_get.return_value = Response(content=f.read().encode("utf-8"))

        races = list(self.ingestor._retrieve_race("2506"))
        self.assertEqual(len(races), 3)
