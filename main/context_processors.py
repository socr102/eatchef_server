def base_url(request):
    """
        Return a BASE_URL template context for the current request.
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return {'BASE_URL': '%s%s' % (scheme, request.get_host())}
