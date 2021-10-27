import re
import os


def remove_keys_with_none(original: dict) -> dict:
    return {k: v for k, v in original.items() if v is not None}


def strip_links(text: str) -> str:
    # text = re.sub('<[^<]+?>', '', text)  # for all tags
    text = re.sub('<a href="(.+)">', '', text)
    text = re.sub('</a>', '', text)
    return text


def is_prod() -> bool:
    return os.environ.get('DJANGO_SETTINGS_MODULE') == 'main.settings.prod'


def is_stage() -> bool:
    return os.environ.get('DJANGO_SETTINGS_MODULE') == 'main.settings.stage'


def is_local() -> bool:
    return os.environ.get('DJANGO_SETTINGS_MODULE') == 'main.settings.local'
