# required for auto-instancing to work
from apps.actions.management.scrappers.arc._v1 import ARCScrapperV1
from apps.actions.management.scrappers.arc._v2 import ARCScrapperV2

from apps.actions.management.scrappers.arc.arc import ARCScrapper

__all__ = [ARCScrapper]
