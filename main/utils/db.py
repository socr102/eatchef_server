from django.db.models import Func


class Round1(Func):
    """
    Postgres-specific round function with precision

    can become unnecessary in Django 3.3
    """
    function = "ROUND"
    template = "%(function)s(%(expressions)s::numeric, 1)"
