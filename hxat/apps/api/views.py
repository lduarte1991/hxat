import logging

from django.conf import settings
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import  BasePermission

from hx_lti_initializer.models import LTICourse
from hxat.apps.api.serializers import LTICourseSerializer
from hxat.apps.vpaljwt.jwt import VpaljwtAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """remove CSRF check."""

    def enforce_csrf(self, request):
        return


class IsAllowed2HxatAPI(BasePermission):
    """checks if user is authenticated via vpaljwt."""

    def has_permission(self, request, view):
        # hack to test/debug  without login
        if settings.DEBUG and settings.HXAT_BYPASS_API_AUTH:
            return True

        # only authenticated users have access
        if request.user and request.user.is_authenticated:
            # was authenticated by vpaljwt?
            if request.auth == ".".join(
                [VpaljwtAuthentication.__module__, VpaljwtAuthentication.__name__]
            ):
                return True

        return False



class LTICourseDetail(generics.RetrieveAPIView):
    queryset = LTICourse.objects.all()
    serializer_class = LTICourseSerializer
    lookup_field = "course_id"

    authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)
    permission_classes = (IsAllowed2HxatAPI,)


class LTICourseList(generics.ListAPIView):
    queryset = LTICourse.objects.all()
    serializer_class = LTICourseSerializer
    lookup_field = "course_id"

    authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)
    permission_classes = (IsAllowed2HxatAPI,)
