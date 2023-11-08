# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone

import jwt
from django.urls import reverse
from rest_framework import authentication, exceptions

from hxat.apps.vpaljwt.models import APIKey

logger = logging.getLogger(__name__)

VPALJWT_REQUIRED_CLAIMS = ("iss", "sub", "iat")
VPALJWT_TIMEDRIFT_IN_SECS = 60


class VpaljwtException(Exception):
    pass


class Vpaljwt(object):
    @classmethod
    def decode(cls, token, secret="", verify=False):
        # decode to get apikey, verify after we have apikey
        payload = jwt.decode(
            token,
            secret,
            options={
                "verify_signature": verify,
                "require": list(VPALJWT_REQUIRED_CLAIMS),
            },
            algorithms=["HS256"],
        )
        return payload

    def __init__(self, encoded_token):
        try:
            jwt_payload = Vpaljwt.decode(encoded_token, verify=False)
        except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError) as e:
            raise VpaljwtException("unable to create Vpaljwt object: {}".format(e))

        # stash jwt claims in instance
        self.payload = jwt_payload
        self.encoded_token = encoded_token
        for c in VPALJWT_REQUIRED_CLAIMS:
            setattr(self, c, jwt_payload[c])

        # always have to have an apikey
        _ = self.fetch_apikey()  # might raise exception

    def __repr__(self):
        return "{}|{}|{}".format(
            getattr(self, "iss", "na"),
            getattr(self, "sub", "na"),
            getattr(self, "iat", "na"),
        )

    def fetch_apikey(self):
        # fetch apikey for jwt
        if getattr(self, "apikey", None) is None:
            try:
                apikey = APIKey._default_manager.get(pk=self.sub)
            except APIKey.DoesNotExist:
                msg = "unknown apikey({}) in vpaljwt".format(self.sub)
                raise VpaljwtException(msg)
            else:
                # stash apikey in instance
                self.apikey = apikey

        return self.apikey

    def validate(self):
        # apikey expired?
        if self.apikey.has_expired():
            msg = "key({}) expired({})".format(self.__repr__(), self.apikey.expire_on)
            raise VpaljwtException(msg)

        # now we can verify signature
        try:
            _ = Vpaljwt.decode(
                self.encoded_token, secret=str(self.apikey.secret), verify=True
            )
        except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError) as e:
            msg = "unable to verify jwt({}) signature: {}".format(self.__repr__(), e)
            raise VpaljwtException(msg)

        # token expired?
        if self.is_expired():
            msg = "jwt({}) expired".format(self.payload)
            raise VpaljwtException(msg)

        # username matches apikey.user?
        if self.iss != self.apikey.user.username:
            msg = "jwt({}) expected user({}), found({})".format(
                self.__repr__(), self.apikey.user.username, self.iss
            )
            raise VpaljwtException(msg)

        return None  # means **is_valid**

    def is_expired(self):
        now = int(datetime.now(tz=timezone.utc).timestamp())

        ttl = self.apikey.valid_for_secs
        if self.iat is None or ttl is None:
            logger.error(
                "missing 'iat'({}) or 'ttl'({})".format(self.payload, self.apikey.key)
            )
            return "missing 'iat'({}) or 'ttl'({})".format(
                self.payload, self.apikey.key
            )
            return True

        expiration = self.iat + ttl
        if expiration < now:
            logger.error("token({}) expired on {}".format(self.payload, expiration))
            return "token({}) expired on {}".format(self.payload, expiration)
            return True

        if self.iat > (now + VPALJWT_TIMEDRIFT_IN_SECS):
            logger.error(
                "token({}) iat in future or timedrift; now({})".format(
                    self.payload, now
                )
            )
            return "token({}) iat in future or timedrift; now({})".format(
                self.payload, now
            )
            return True

        return False


def encode_token(payload, secret):
    return jwt.encode(payload, secret, algorithm="HS256")


def encode_vpaljwt(apikey, iat=None):
    payload = {
        "iss": apikey.user.username,
        "sub": str(apikey.key),
        "iat": iat if iat else int(datetime.now(tz=timezone.utc).timestamp()),
    }
    return encode_token(payload, str(apikey.secret))


class VpaljwtAuthentication(authentication.BaseAuthentication):
    """Authenticate against the jwt in request.

    Add to list of DEFAULT_AUTHENTICATION_CLASSES in settings.REST_FRAMEWORK,
    or to each view in authentication_classes tuple.

    expected jwt payload: {
        "iss": "api client id",    # username
        "sub": "api key",          # uuid
        "iat": "issuing time",     # timestamp integer!
    }
    """

    def authenticate(self, request):
        if getattr(request, "vpaljwt", None) is None:
            return None  # nothing to be done

        try:
            jwt = Vpaljwt(request.vpaljwt)
        except VpaljwtException as e:
            logger.error("jwt present but cannot decode: {}".format(e))
            return None

        try:
            jwt.validate()
        except VpaljwtException as e:
            logger.error("jwt present but invalid: {}".format(e))
            return None

        # check if requested path (app) is allowed for this apikey
        if request.path not in jwt.apikey.audience and request.path != reverse(
            "vpaljwt:allowedendpoints"
        ):
            logger.error(
                "jwt present but audience invalid: got({}), expected({})".format(
                    request.path, jwt.apikey.audience
                )
            )
            raise exceptions.AuthenticationFailed("forbidden resource")

        return (
            jwt.apikey.user,
            ".".join(
                [VpaljwtAuthentication.__module__, VpaljwtAuthentication.__name__]
            ),
        )
