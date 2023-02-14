"""oauth validators for lti."""

import logging
from uuid import uuid4

from django.conf import settings
from oauthlib.common import to_unicode
from oauthlib.oauth1 import RequestValidator

log = logging.getLogger(__name__)


class LTIRequestValidator(RequestValidator):
    @property
    def enforce_ssl(self):
        return getattr(settings, "HXLTI_ENFORCE_SSL", False)

    @property
    def dummy_client(self):
        client = getattr(settings, "HXLTI_DUMMY_CONSUMER_KEY", "DUMMY_CONSUMER_KEY")
        return to_unicode(client)

    @property
    def dummy_secret(self):
        secret = LTIRequestValidator.make_dummy_secret()
        return secret

    def check_client_key(self, key):
        # redefine: any non-empty string is OK as a client key
        return len(key) > 0

    def check_nonce(self, nonce):
        # redefine: any non-empty string is OK as a nonce
        return len(nonce) > 0

    def validate_client_key(self, client_key, request):
        # hxat uses a compound consumer_key with context_id
        context_id = request.body.get("context_id", None)
        if context_id is not None and context_id in settings.LTI_SECRET_DICT:
            return client_key == settings.CONSUMER_KEY

        if client_key == getattr(settings, "CONSUMER_KEY", "DUMMY_CONSUMER_KEY"):
            return True
        else:
            return False

    def validate_timestamp_and_nonce(
        self,
        client_key,
        timestamp,
        nonce,
        request,
        request_token=None,
        access_token=None,
    ):
        return True

    def get_client_secret(self, client_key, request):
        # might use a compound consumer_key with context_id
        context_id = request.body.get("context_id", None)
        return LTIRequestValidator.fetch_lti_secret(
            client_key=client_key, context_id=context_id
        )

    @classmethod
    def make_dummy_secret(cls):
        return getattr(settings, "HXLTI_DUMMY_SECRET", uuid4().hex)

    @classmethod
    def fetch_lti_secret(cls, client_key, context_id=None):
        if context_id is None:
            log.error('missing lti-param "context_id"; dummy.')
            return cls.make_dummy_secret()

        try:
            secret = to_unicode(settings.LTI_SECRET_DICT[context_id])
        except KeyError:  # context_id not in LTI_SECRET_DICT
            if client_key == settings.CONSUMER_KEY:
                log.debug("----------------- lti consumer key FALLBACK")
                return to_unicode(settings.LTI_SECRET)
            else:  # oauth_consumer_key not a known value
                log.error(
                    "unknown client-key({}) in lti-params; dummy.".format(client_key)
                )
                return cls.make_dummy_secret()
        else:  # all went well
            return secret


# TODO: for another example on how to use pylti, check validators in
# https://github.com/nmaekawa/hxlti-djapp
