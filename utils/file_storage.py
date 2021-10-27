import mimetypes
import os
from hashlib import md5
from pathlib import Path


def banner_image_file_path(instance, filename):
    return f'b_images/{get_filename_by_hash(instance.image, filename)}'


def block_image_file_path(instance, filename):
    return f'block_images/{get_filename_by_hash(instance.image, filename)}'


def recipe_image_file_path(instance, filename):
    return f'recipe_files/{instance.recipe.pk}/{get_filename_by_hash(instance.file.file, filename)}'


def recipe_new_image_file_path(instance, filename):
    return f'recipe_image_files/{instance.user.pk}/{get_filename_by_hash(instance.file.file, filename)}'


def recipe_thumbnail_file_path(instance, filename):
    return f'recipe_thumbnails/{instance.user.pk}/{Path(filename).name}'


def recipe_video_file_path(instance, filename):
    return f'recipe_video/{instance.user.pk}/{get_filename_by_hash(instance.video.file, filename)}'


def role_model_image_file_path(instance, filename):
    return f'role_model_files/{instance.user.pk}/{get_filename_by_hash(instance.file.file, filename)}'


def chef_pencil_image_file_path(instance, filename):
    return f'chef_pencils/{get_filename_by_hash(instance.image, filename)}'


def get_filename_by_hash(file, filename) -> str:
    file.seek(0)
    file_hash = md5(file.read()).hexdigest()
    return f"{file_hash}.{filename.split('.')[-1]}"


def get_file(instance, prop_name=None):
    if prop_name is not None:
        return getattr(instance, prop_name).file
    return instance.file.file


def delete_image(image):
    return image.delete(True)


def get_storage_path_unique(instance, filename, directory):
    filename_hash = get_filename_by_hash(get_file(instance, 'sample'), filename)
    return f"{directory}/{filename_hash[0:10]}/{filename_hash[10:]}"


def get_storage_path_static(key, filename, directory):
    return f"{directory}/{key}/{filename}"


def avatar_property_avatar_path(instance, filename):
    return get_storage_path_static(
        instance.pk,
        get_filename_by_hash(instance.avatar, filename),
        'avatars'
    )


def preview_property_preview_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    return get_storage_path_static(instance.pk, f"preview{file_extension}", 'previews')


def get_file_mime(filename):
    return mimetypes.guess_type(filename)