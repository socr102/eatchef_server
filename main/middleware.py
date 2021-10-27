from django.utils import timezone
from django.utils.timezone import get_default_timezone
import pytz
import logging
import sys
import datetime
import uuid


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO для дальнейшего расширения, необходимо будет определять тайм зону пользователя
        tzname = get_default_timezone()
        if tzname:
            timezone.activate(pytz.timezone(tzname.zone))
        else:
            timezone.deactivate()
        return self.get_response(request)


class RequestTimeLoggingMiddleware:
    """Middleware class logging request time to stderr.

    This class can be used to measure time of request processing
    within Django.  It can be also used to log time spent in
    middleware and in view itself, by putting middleware multiple
    times in INSTALLED_MIDDLEWARE.

    Static method `log_message' may be used independently of the
    middleware itself, outside of it, and even when middleware is not
    listed in INSTALLED_MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_request(self, request):
        self.log_message(request, 'request ')

    def process_response(self, request, response):
        s = getattr(response, 'status_code', 0)
        r = str(s)
        if s in (300, 301, 302, 307):
            r += ' => %s' % response.get('Location', '?')
        elif hasattr(response, 'content'):
            r += ' (%db)' % len(response.content)
        self.log_message(request, 'response', r)
        return response

    @staticmethod
    def log_message(request, tag, message=''):
        """Log timing message to stderr.

        Logs message about `request' with a `tag' (a string, 10
        characters or less if possible), timing info and optional
        `message'.

        Log format is "timestamp tag uuid count path +delta message"
        - timestamp is microsecond timestamp of message
        - tag is the `tag' parameter
        - uuid is the UUID identifying request
        - count is number of logged message for this request
        - path is request.path
        - delta is timedelta between first logged message
          for this request and current message
        - message is the `message' parameter.
        """
        dt = datetime.datetime.utcnow()
        if not hasattr(request, '_logging_uuid'):
            request._logging_uuid = uuid.uuid1()
            request._logging_start_dt = dt
            request._logging_pass = 0

        request._logging_pass += 1
        delta = dt - request._logging_start_dt
        print(
            '{date} {tag} {id} {num} {method} {path}{message}{delta}'.format(
                date=dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
                tag=tag,
                id=request._logging_uuid,
                num=request._logging_pass,
                method=request.method,
                path=request.get_full_path(),
                message='' if not message else f' {message}',
                delta='' if delta == datetime.timedelta(seconds=0) else f' {delta.total_seconds()}'
            ),
            file=sys.stdout
        )
        # print(request.body)

