# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib import auth

from hxat.apps.vpaljwt.jwt import VpaljwtAuthentication

PRINT_JWT_ERROR = getattr(settings, "VPALJWT_LOG_JWT_ERROR", False)
PRINT_JWT = getattr(settings, "VPALJWT_LOG_JWT", False)

logger = logging.getLogger(__name__)


class VpaljwtMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """get jwt info into request."""

        # get token from request header
        credentials = VpaljwtMiddleware.get_credentials(request)
        if credentials is not None:
            if PRINT_JWT:
                logger.info("jwt token: {}".format(credentials))
            # set vpaljwt attribute in request
            request.vpaljwt = (
                credentials.decode() if isinstance(credentials, bytes) else credentials
            )
        else:
            if PRINT_JWT_ERROR:
                logger.info("failed to find auth token in request header")

        response = self.get_response(request)

        # logout user if authenticated with vpaljwt, because stateless!
        if getattr(request, "user", None) is not None:
            if request.user.is_authenticated and getattr(request, "auth", None):
                if PRINT_JWT:
                    logging.getLogger(__name__).info(
                        "user({}) and auth({}) readty to logout".format(
                            request.user.username, request.auth
                        )
                    )
                if request.auth == ".".join(
                    [VpaljwtAuthentication.__module__, VpaljwtAuthentication.__name__]
                ):
                    auth.logout(request)  # logout user

        return response

    @classmethod
    def get_credentials(cls, request):
        """get jwt token from http header."""
        credentials = None
        header = request.META.get(settings.VPALJWT_HTTP_HEADER, None)
        if header:
            (auth_scheme, token) = header.split()
            if auth_scheme.lower() == "bearer":
                # Work around django test client oddness:
                # https://github.com/jpadilla/django-jwt-auth/blob/master/jwt_auth/utils.py
                if isinstance(auth_scheme, type("")):
                    credentials = token.encode("iso-8859-1")
                else:
                    credentials = token
        return credentials
