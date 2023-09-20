import json
import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from hxat.apps.api.serializers import LTICourseSerializer



class CsrfExemptSessionAuthentication(SessionAuthentication):
    """remove CSRF check."""

    def enforce_csrf(self, request):
        return


class LTICourseDetail(generics.RetrieveAPIView):
    serializer_class = LTICourseSerializer
    lookup_field = "course_id"

    authentication_classes = (CsrfExemptSessionAuthentication)
    #authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)
    #permission_classes = (IsKondoEditorOrReadOnly,)


