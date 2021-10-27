from rest_framework.exceptions import ValidationError


class UrlDomainValidator:
    def __init__(self, domain):
        self.domain = domain

    def __call__(self, value):
        url = value
        domain = "https://" + self.domain
        www_domain = "https://www." + self.domain
        if domain not in url and www_domain not in url:
            raise ValidationError('The link {} must contain {}'.format(url, self.domain))
