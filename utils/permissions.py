import re


def is_email(string):
    return bool(re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', string, re.I))


def is_phone_number(string):
    return bool(re.search(r'\+\d*\s\(\d*\)\s\d', string))
