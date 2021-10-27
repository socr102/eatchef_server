from main.watermark_storage import WatermarkStorage
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings.local")
django.setup()
from pathlib import Path

from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
from recipe.models import Recipe



def main():

    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(
            settings.BASE_DIR,
            'settings',
            'atomic-dahlia-316917-740b0b638ed2.json'
        )
    )
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(settings.GS_BUCKET_NAME)

    tmp_dir = Path(settings.PROJECT_DIR) / 'tmp'
    tmp_dir.mkdir(exist_ok=True)

    for r in Recipe.objects.all():
        for ri in r.images.all():

            if not ri.new_file:

                print("file", ri.file.name)
                blob = ri.file.storage.bucket.blob('media/' + ri.file.name)

                # download to file
                downloaded_file_path = Path(settings.PROJECT_DIR).joinpath(f"tmp/{ri.file.name.split('/')[-1]}")
                blob.download_to_filename(downloaded_file_path)

                # add watermark
                try:
                    WatermarkStorage().add_watermark(downloaded_file_path)
                except Exception as e:
                    print(e)

                # determine new name
                file_name = ri.file.name.split('/')[-1]
                new_name = f'recipe_image_files/{r.user.pk}/{file_name}'
                print(new_name)

                # upload file to the new path
                blob = bucket.blob('media/' + new_name)
                blob.upload_from_filename(downloaded_file_path)

                # save this new path as new_file field
                ri.new_file.name = new_name
                ri.user = r.user
                ri.save()

                # remove tmp file with watermark
                # downloaded_file_path.unlink()

                """
                ri.new_file.name = new_name
                ri.user = r.user
                ri.save()

                ri.file_storage.bucket.

                ri.file.storage.bucket.copy_blob(
                    ri.file.storage.bucket.blob('media/' + ri.file.name),
                    ri.file.storage.bucket,
                    new_name
                )

                print(ri.file.storage.bucket.blob('media/' + ri.new_file.name))
                # print(ri.file.storage.bucket.blob('media/' + ri.new_file.name).path)
                print(ri.file.storage.url(name=ri.new_file.name))

                # delete old blobs
                ri.file.storage.bucket.blob('media/' + ri.file.name).delete()
                """

if __name__ == '__main__':
    main()
