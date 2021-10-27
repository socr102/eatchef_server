from django.core.validators import FileExtensionValidator, RegexValidator
from mutagen import File
from rest_framework.exceptions import ValidationError

validate_phone = RegexValidator(
    regex=r'^((\+1|\+7|)\d{3}\d{3}\d{4})$',
    message="Enter the correct phone number"
)

validate_phone_simple = RegexValidator(
    regex=r'^([0-9]+)$',
    message="Enter the correct phone number"
)

validate_ep_document = FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xlsx', 'xls'])

validate_ep_schema = FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])

validate_deal_file = FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'])

validate_video_ext = FileExtensionValidator(allowed_extensions=['mp4'])


def validate_max_count_files(value, max_count):
    if len(value) > max_count:
        raise ValidationError(
            f"The number of files cannot exceed {max_count}")
    return value


def validate_avatar_max_size(value):
    file_size = value.size
    file_size_limit_mb = 10
    limit_kb = file_size_limit_mb * 1024 * 1024
    if file_size > limit_kb:
        raise ValidationError("Maximum file size %s MB" % file_size_limit_mb)


def validate_images_file_max_size(value):
    file_size = value.size
    file_size_limit_mb = 10
    limit_kb = file_size_limit_mb * 1024 * 1024
    if file_size > limit_kb:
        raise ValidationError("Maximum file size %s MB" % file_size_limit_mb)


def validate_video_file_max_size(value):
    file_size = value.size
    file_size_limit_mb = 200
    limit_kb = file_size_limit_mb * 1024 * 1024
    if file_size > limit_kb:
        raise ValidationError("Maximum file size %s MB" % file_size_limit_mb)


def validate_preview_file_max_size(value):
    file_size = value.size
    file_size_limit_mb = 10
    limit_kb = file_size_limit_mb * 1024 * 1024
    if file_size > limit_kb:
        raise ValidationError("Maximum file size %s MB" % file_size_limit_mb)

validate_youtube = RegexValidator(
    regex=r'youtube.com|youtu.be',
    message='Only YouTube videos allowed'
)

validate_only_numbers = RegexValidator(regex=r'^\d+$', message='The field must contain only numbers')


def validate_decimals(value):
    if len(str(value).split('.')[-1]) > 3:
        raise ValidationError({'quantity': "The value should have maximum 3 numbers after the dot"})
    return value
