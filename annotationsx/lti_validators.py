"""oauth validators for lti."""

import logging
from oauthlib.oauth1 import RequestValidator
from oauthlib.oauth1 import SIGNATURE_HMAC
from oauthlib.common import to_unicode
import redis

from django.conf import settings
from django.http import HttpRequest


log = logging.getLogger(__name__)


class LTIRequestValidator(RequestValidator):

    @property
    def enforce_ssl(self):
        return getattr(settings, 'HXLTI_ENFORCE_SSL', False)

    @property
    def dummy_client(self):
        client = getattr(settings, 'HXLTI_DUMMY_CONSUMER_KEY', 'DUMMY_CONSUMER_KEY')
        return to_unicode(client)

    @property
    def dummy_secret(self):
        secret = getattr(settings, 'HXLTI_DUMMY_SECRET', 'DUMMY_SECRET')
        return to_unicode(secret)

    def check_client_key(self, key):
        # redefine: any non-empty string is OK as a client key
        return len(key) > 0


    def check_nonce(self, nonce):
        # redefine: any non-empty string is OK as a nonce
        return len(nonce) > 0


    def validate_client_key(self, client_key, request):
        if client_key in getattr(settings, 'LTI_SECRET_DICT', None):
            return True

        if client_key == getattr(settings, 'CONSUMER_KEY', 'DUMMY_CONSUMER_KEY'):
            return True
        else:
            return False


    def validate_timestamp_and_nonce(
        self, client_key, timestamp, nonce,
        request, request_token=None, access_token=None):
        return True


    def get_client_secret(self, client_key, request):
        c = getattr(settings.LTI_SECRET_DICT, client_key, None)
        if c:
            return to_unicode(getattr(setting.LTI_SECRET_DICT[c], None))  # make sure secret val is unicode

        # assumes that if CONSUMER_KEY not defined, then LTI_SECRET also not defined
        if client_key == getattr(settings, 'CONSUMER_KEY', self.dummy_client):
            return to_unicode(getattr(settings, 'LTI_SECRET', self.dummy_secret))


# TODO: for a better example on how to use pylti, check validators in
# https://github.com/nmaekawa/hxlti-djapp

