import logging

from hx_lti_initializer.models import LTICourse
from hxat.apps.api.serializers import LTICourseSerializer
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """remove CSRF check."""

    def enforce_csrf(self, request):
        return


class LTICourseDetail(generics.RetrieveAPIView):
    queryset = LTICourse.objects.all()
    serializer_class = LTICourseSerializer
    lookup_field = "course_id"

    authentication_classes = (CsrfExemptSessionAuthentication,)
    # authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)
    # permission_classes = (IsKondoEditorOrReadOnly,)

class LTICourseList(generics.ListAPIView):
    queryset = LTICourse.objects.all()
    serializer_class = LTICourseSerializer
    lookup_field = "course_id"

    authentication_classes = (CsrfExemptSessionAuthentication,)
    # authentication_classes = (CsrfExemptSessionAuthentication, VpaljwtAuthentication)
    # permission_classes = (IsKondoEditorOrReadOnly,)
