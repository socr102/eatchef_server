import random
import string
from binascii import crc32
from datetime import datetime

from django.db.models import Model


def random_simple_string(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_with_n_digits(n) -> int:
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return random.randint(range_start, range_end)


def random_us_international_phone_number() -> str:
    return '+1' + str(random_with_n_digits(10))


def generate_unique_code(cls_model, field: str, length: int) -> str:
    issubclass(cls_model, Model)

    raw_code = random_simple_string(length)

    while cls_model.objects.filter(**{field: raw_code}).exists():
        raw_code = random_simple_string(length)
    return raw_code


def generate_referral_code(value: int):
    return hex(crc32(bytes(value))).replace('0x', '').upper()


def generate_unique_hash_by_timestamp(key) -> str:
    salt = f'{key}-{str(datetime.now().timestamp())}'
    return hex(crc32(bytes(salt, encoding='utf8'))).replace('0x', '').upper()
