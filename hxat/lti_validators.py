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

        # DB-first: check LTICourseCredential table
        if context_id is not None:
            try:
                from hx_lti_initializer.models import LTICourse, LTICourseCredential
                course = LTICourse.get_course_by_id(context_id)
                try:
                    cred = LTICourseCredential.objects.get(course=course)
                    # credential exists — reject if inactive regardless of dict
                    if cred.deactivated or not cred.approved:
                        return False
                    return client_key == cred.lti_key
                except LTICourseCredential.DoesNotExist:
                    pass  # no credential yet, fall through to dict/global
            except LTICourse.DoesNotExist:
                pass
            except Exception:
                log.warning("DB error during client key validation for %s", context_id)

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

        # DB-first: single course lookup shared by both the credential check and
        # the auto-migrate path below
        from hx_lti_initializer.models import LTICourse, LTICourseCredential
        course = None
        try:
            course = LTICourse.get_course_by_id(context_id)
            cred = LTICourseCredential.objects.get(course=course)
            if cred.deactivated or not cred.approved:
                return cls.make_dummy_secret()
            return to_unicode(cred.lti_secret)
        except LTICourseCredential.DoesNotExist:
            pass  # course found, no credential yet — fall through
        except LTICourse.DoesNotExist:
            pass  # unknown course — fall through
        except Exception:
            log.warning("DB error during secret lookup for %s", context_id)

        # Dict fallback: use dict value and auto-promote to DB
        if context_id in settings.LTI_SECRET_DICT:
            secret = to_unicode(settings.LTI_SECRET_DICT[context_id])
            if course is not None:
                try:
                    LTICourseCredential.objects.get_or_create(
                        course=course,
                        defaults={
                            "lti_secret": secret,
                            "approved": True,
                        },
                    )
                except Exception as e:
                    log.warning("auto-migrate LTI_SECRET_DICT to DB failed for %s: %s", context_id, e)
            return secret

        if client_key == settings.CONSUMER_KEY:
            log.debug("----------------- lti consumer key FALLBACK")
            return to_unicode(settings.LTI_SECRET)
        else:  # oauth_consumer_key not a known value
            log.error(
                "unknown client-key({}) in lti-params; dummy.".format(client_key)
            )
            return cls.make_dummy_secret()


# TODO: for another example on how to use pylti, check validators in
# https://github.com/nmaekawa/hxlti-djapp
