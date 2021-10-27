from django.conf import settings


def get_base_url_with_path(path: str):
    return '%s%s' % (settings.BASE_URL, path)
