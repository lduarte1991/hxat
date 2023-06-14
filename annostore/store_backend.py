import logging

import requests
from annostore.store import Annostore
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from hx_lti_initializer.utils import retrieve_token

logger = logging.getLogger(__name__)


class CatchpyBackend(Annostore):
    def __init__(self, request, asconfig):
        super().__init__(request, asconfig)
        self.timeout = 5.0  # timeout for most actions, other than search perhaps
        self.headers = {"content-type": "application/json"}
        self.headers["authorization"] = "token " + retrieve_token(
            userid=request.LTI["hx_user_id"],
            apikey=self.asconfig[1],
            secret=self.asconfig[2],
            ttl=120,  # 2m
        )

    def _get_database_url(self, path="/"):
        base_url = self.asconfig[0]
        return "{}{}".format(base_url, path)

    def _response_timeout(self):
        return JsonResponse({"error": "request timeout"}, status=500)

    def _response_from_catchpy(self, response):
        if (
            response.headers.get("content-type", None)
            and "application/json" in response.headers["content-type"]
        ):
            return JsonResponse(data=response.json(), status=response.status_code)
        else:
            return HttpResponse(
                response.content,
                status=response.status_code,
                content_type=response.headers.get("content-type", "text/plain"),
            )

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
                apikey=self.asconfig[1],
                secret=self.asconfig[2],
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
        return self._response_from_catchpy(response)

    # implemented for completion; hxat does not support READ requests!
    def read(self, annotation_id):
        database_url = self._get_database_url("/{}".format(annotation_id))
        self.logger.info(
            "read: url({}) headers({}) id({})".format(
                database_url, self.headers, annotation_id
            )
        )
        try:
            response = requests.get(
                database_url, headers=self.headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "read: url({}) headers({}) exc({})".format(
                    database_url, self.headers, e
                )
            )
            return self._response_timeout()
        self.logger.info(
            "read: url({}) headers({}) status({})".format(
                database_url, self.headers, response.status_code
            )
        )
        return self._response_from_catchpy(response)

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
        return self._response_from_catchpy(response)

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
        return self._response_from_catchpy(response)

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
        return self._response_from_catchpy(response)

    def transfer(self, transfer_params):
        database_url = self._get_database_url("/copy")
        self.logger.info(
            "copy: url({}) headers({}) params({})".format(
                database_url,
                self.headers,
                transfer_params,
            )
        )
        self.logger.info(
            "adds override in transfer({})->({}) jwt({})".format(
                transfer_params["source_collection_id"],
                transfer_params["target_collection_id"],
                list(transfer_params["userid_map"].values())[0],
            )
        )
        self.headers["authorization"] = "token " + retrieve_token(
            list(transfer_params["userid_map"].values())[0],
            apikey=self.asconfig[1],
            secret=self.asconfig[2],
            ttl=300,  # 5m
            override=["CAN_COPY"],
        )
        try:
            response = requests.post(
                database_url,
                json=transfer_params,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as e:
            self.logger.error(
                "copy: url({}) headers({}) data({}) exc({})".format(
                    database_url, self.headers, transfer_params, e
                )
            )
            return self._response_timeout()
        self.logger.info(
            "transfer: url({}) headers({}) status({})".format(
                database_url, self.headers, response.status_code
            )
        )
        return self._response_from_catchpy(response)


###################################################################################
