import os
import sys
from io import BytesIO

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

from utils.file_storage import get_file_mime


class WatermarkStorage(FileSystemStorage):

    WATERMARK_PATH = os.path.join(
        settings.STATIC_ROOT,
        'recipe',
        'watermark.png'
    )

    @property
    def _margin(self):
        return 16

    def add_watermark(self, image_path):
        watermark = Image.open(self.WATERMARK_PATH)
        temp_image = Image.open(image_path)

        bi_width, bi_height = temp_image.size
        w_width, w_height = watermark.size
        x = bi_width - w_width - self._margin
        y = bi_height - w_height - self._margin

        mime_type = get_file_mime(image_path)

        name, extension = os.path.splitext(image_path)
        temp_image.paste(watermark, (x, y), watermark)
        temp_image.save(image_path, format=temp_image.format)
