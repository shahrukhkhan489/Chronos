# Generate a referrer link based on the request with a fallback
from flask import request, url_for


def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)
