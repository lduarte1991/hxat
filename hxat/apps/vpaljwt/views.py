import logging

from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from hxat.apps.vpaljwt.jwt import VpaljwtAuthentication

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """remove CSRF check."""

    def enforce_csrf(self, request):
        return


class AllowedEndpoints(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)

    def get(self, request):
        if request.auth != ".".join(
            [VpaljwtAuthentication.__module__, VpaljwtAuthentication.__name__]
        ):
            return Response(data={}, status=403)  # not allowed without jwt

        return Response(request.user.apikey.audience)
