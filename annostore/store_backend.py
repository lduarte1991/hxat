import logging

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse

from annotation_store.store import AnnotationStore
from hx_lti_initializer.utils import retrieve_token

logger = logging.getLogger(__name__)


class WebAnnotationStoreBackend(AnnotationStore):
    def __init__(self, request, course, assignment, store_cfg):
        super().__init__(request, course, assignment, store_cfg)
        self.timeout = 5.0  # timeout for most actions, other than search perhaps
        self.headers = {"content-type": "application/json"}
        self.headers["authorization"] = "token " + retrieve_token(
            userid=request.LTI["hx_user_id"],
            apikey=self.store_cfg.apikey,
            secret=self.store_cfg.secret,
            ttl=60,  # 2m
        )

    def _get_database_url(self, path="/"):
        base_url = self.store_cfg.url
        return "{}{}".format(base_url, path)

    def _response_timeout(self):
        return JsonResponse({"error": "request timeout"}, status=500)

    def before_search(self):
        # Override the auth token when the user is a course administrator, so they can query annotations
        # that have set their read permissions to private (i.e. read: self-only).
        # Note: this only works if the annotation store accepts the ADMIN_GROUP_ID as superuser
        # - this is true for catchpy, who allows any operation when use is  "__admin__" (default
        # value, ADMIN_GROUP_ID is configurable in catchpy) in jwt.
        if self.request.LTI["is_staff"]:
            self.logger.info("updating auth token for admin")
            self.headers["authorization"] = "token " + retrieve_token(
                userid=settings.ADMIN_GROUP_ID,
                apikey=self.store_cfg.apikey,
                secret=self.store_cfg.secret,
                ttl=300,  # 5m
            )

    def search(self):
        # add perms for admin access to private annotations
        self.before_search()

        timeout = 10.0
        params = self.request.GET.urlencode()
        database_url = self._get_database_url("/")
        try:
            response = requests.get(
                database_url, headers=self.headers, params=params, timeout=timeout
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "search: url({}) headers({}) params({}) timeout({}) exc({})".format(
                    database_url, self.headers, params, timeout, e
                )
            )
            return self._response_timeout()

        self.logger.info(
            "search: url({}) headers({}) params({}) timeout({}) status({}) content_length({})".format(
                database_url,
                self.headers,
                params,
                timeout,
                response.status_code,
                response.headers.get("content-length", 0),
            )
        )
        response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type="application/json",
        )
        return response

    def create(self, annotation_id):
        database_url = self._get_database_url("/{}".format(annotation_id))
        data = self.request.body
        self.logger.info(
            "create: url({}) headers({}) data({})".format(
                database_url, self.headers, data
            )
        )
        try:
            response = requests.post(
                database_url, data=data, headers=self.headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "create: url({}) headers({}) data({}) exc({})".format(
                    database_url, self.headers, data, e
                )
            )
            return self._response_timeout()
        self.logger.info(
            "create: url({}) headers({}) data({}) status({})".format(
                database_url, self.headers, data, response.status_code
            )
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type="application/json",
        )

    def update(self, annotation_id):
        database_url = self._get_database_url("/%s" % annotation_id)
        data = self.request.body
        self.logger.info(
            "update: url({}) headers({}) data({})".format(
                database_url, self.headers, data
            )
        )
        try:
            response = requests.put(
                database_url, data=data, headers=self.headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "update: url({}) headers({}) data({}) exc({})".format(
                    database_url, self.headers, data, e
                )
            )
            return self._response_timeout()
        self.logger.info(
            "update: url({}) headers({}) data({}) status({})".format(
                database_url, self.headers, data, response.status_code
            )
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type="application/json",
        )

    def delete(self, annotation_id):
        database_url = self._get_database_url("/{}".format(annotation_id))
        self.logger.info(
            "delete: url({}) headers({}) id({})".format(
                database_url, self.headers, annotation_id
            )
        )
        try:
            response = requests.delete(
                database_url, headers=self.headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "update: url({}) headers({}) exc({})".format(
                    database_url, self.headers, e
                )
            )
            return self._response_timeout()
        self.logger.info(
            "delete: url({}) headers({}) status({})".format(
                database_url, self.headers, response.status_code
            )
        )
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type="application/json",
        )


###################################################################################

"""
05mar20 naomi: (item1) right now the assumption is that, at least at course
level, all assignments use the same backend config (same url and credentials).
This is tacit and not enforced in code, we are blindly trusting in the random
goodness of users hearts. This requirement allows developers to create
assignemnts with lti components pointing to other lti providers than prod and
do debugging and tests.

"""
