from apps.actions.digesters.ocr._image import ImageOCR, OCRDatasource

# required for auto-instancing to work
from apps.actions.digesters.ocr.inforemo import ImageOCRInforemo

__all__ = [ImageOCR, OCRDatasource]
