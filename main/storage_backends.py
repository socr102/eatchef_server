import os
import sys
from io import BytesIO
import subprocess
import tempfile
from pathlib import Path
from django.conf import settings

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.exceptions import ValidationError
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import setting
from recipe.tasks import create_thumbnail_for_video

from utils.file_storage import get_file_mime

import logging
logger = logging.getLogger('django')


def resize_image(image, width=1200, height=1200):
    temp_image = Image.open(image)
    mime_type = get_file_mime(image.name)
    name, extension = os.path.splitext(image.name)
    outputIoStream = BytesIO()
    temp_image.thumbnail((width, height), Image.ANTIALIAS)
    temp_image.save(outputIoStream, format=temp_image.format)
    outputIoStream.seek(0)
    return InMemoryUploadedFile(
        outputIoStream,
        'ImageField',
        "%s%s" % (name, extension), mime_type[0],
        sys.getsizeof(outputIoStream),
        None
    )


def rotate_image(image):
    temp_image = Image.open(image.original_image)
    mime_type = get_file_mime(image.name)
    name, extension = os.path.splitext(image.name)
    save_format = 'PNG' if extension == '.png' else 'JPEG'
    outputIoStream = BytesIO()
    temp_image = temp_image.rotate(-90, Image.NEAREST, expand=1)
    temp_image.save(outputIoStream, format=save_format)
    outputIoStream.seek(0)
    temp_image.close()
    remove_lot_image(image)
    return InMemoryUploadedFile(
        outputIoStream,
        'ImageField',
        "%s%s" % (name, extension), mime_type[0],
        sys.getsizeof(outputIoStream),
        None
    )


def remove_lot_image(image):
    if image.original_image:
        image.original_image.delete(False)
    if image.image:
        image.image.delete(False)
    if image.thumbnail:
        image.thumbnail.delete(False)


def remove_lot_file(instance):
    if instance.file:
        instance.file.delete(False)


class MediaStorage(GoogleCloudStorage):
    """
    Customized MediaStorage with auto-creation of thumbnail for video with watermark
    before uploading video file to the cloud.

    An image is automatically saved to the RecipeVideo object after creating.
    """

    location = setting('GS_LOCATION')
    file_overwrite = False

    def _save(self, name, content):

        # TODO: move this code to custom field later and possibly use only 1 tmp file

        # for RecipeVideo
        if name.startswith('recipe_video/'):

            # save locally to create thumbnail (video then will be manually deleted)
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.mp4',
                delete=False
            )

            with open(temp_file.name, 'wb+') as df:
                for chunk in content.chunks():
                    df.write(chunk)

            # advanced file checks which require file to be saved

            # size check
            MAX_SIZE = 200 * 1024 * 1024
            size = Path(temp_file.name).stat().st_size
            if size > MAX_SIZE:
                Path(temp_file.name).unlink()
                raise ValidationError({'video': f'Video size ({size}) should be less than or equal to {MAX_SIZE} bytes'})

            # duration check
            MAX_DURATION = 30
            try:
                duration = self.get_video_duration(temp_file.name)
            except Exception:
                Path(temp_file.name).unlink()
                raise ValidationError({'video': 'Incorrect duration'})
            else:
                if duration > MAX_DURATION:
                    Path(temp_file.name).unlink()
                    raise ValidationError(
                        {'video': f'Video duration ({duration} sec) should be less than or equal to {MAX_DURATION} sec'})

        # upload to cloud
        res = super()._save(name, content)

        # for RecipeVideo
        if name.startswith('recipe_video/'):

            create_thumbnail_for_video.delay(
                tmp_video_path=temp_file.name,
                new_name=Path(name).with_suffix('.png').name
            )

        return res

    def get_video_duration(self, filename: str) -> float:
        """
        in seconds

        ffmpeg is required
        """
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filename,
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout)
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))
