import json
import os
import random
import re
import time

import requests
from locust import TaskSet, between, events, task
from lti import ToolConsumer
from utils import fresh_ann
from wsclient import SocketClient

# key: collection_id; value: list of target_object_ids as str
COLLECTION_TARGET_DICT = json.loads(os.environ.get("COLLECTION_TARGET_DICT", "{}"))


def hxat_create(locust):
    catcha = fresh_ann(locust.hxat_client)

    anno_id = catcha["id"]
    params = {
        "resource_link_id": locust.hxat_client.resource_link_id,
        "utm_source": locust.hxat_client.utm_source,
        "version": "catchpy",
    }
    target_path = "/annotation_store/api/{}?".format(anno_id)
    response = locust.client.post(
        target_path,
        json=catcha,
        catch_response=True,
        name="/annotation_store/api/create",
        headers={
            "Content-Type": "Application/json",
            "x-annotator-auth-token": locust.hxat_client.store_token,
            "Referer": "https://naomi.hxat.hxtech.org/lti_init/launch_lti/",
        },
        params=params,
        verify=locust.ssl_verify,
    )
    if response.content == "":
        response.failure("no data")
    else:
        try:
            a_id = response.json()["id"]
        except KeyError:
            resp = response.json()
            if "payload" in resp:
                response.failure(resp["payload"])
            else:
                response.failure("no id in response")
            return
        except json.decoder.JSONDecodeError as e:
            response.failure(e)
            return
        else:
            response.success()


def hxat_search(locust, limit=50, offset=0):
    params = {
        "resource_link_id": locust.hxat_client.resource_link_id,
        "utm_source": locust.hxat_client.utm_source,
        "version": "catchpy",
        "limit": limit,
        "offset": offset,
        "media": "text",
        "source_id": locust.hxat_client.target_source_id,
        "context_id": locust.hxat_client.context_id,
        "collection_id": locust.hxat_client.collection_id,
    }
    target_path = "/annotation_store/api/"
    response = locust.client.get(
        target_path,
        catch_response=True,
        name="/annotation_store/api/search",
        headers={
            "Content-Type": "Application/json",
            "x-annotator-auth-token": locust.hxat_client.store_token,
            "Referer": "https://naomi.hxat.hxtech.org/lti_init/launch_lti/",
        },
        params=params,
        verify=locust.ssl_verify,
    )
    if response.content == "":
        response.failure("no data")
    else:
        try:
            rows = response.json()["rows"]
        except KeyError:
            resp = response.json()
            if "payload" in resp:
                response.failure(resp["payload"])
            else:
                response.failure("missing rows in search response")
            return
        except json.decoder.JSONDecodeError as e:
            response.failure(e)
            return
        else:
            response.success()


def hxat_get_static(locust, url_path):
    target_path = os.path.join("/static/", url_path)
    response = locust.client.get(
        target_path,
        catch_response=True,
        cookies={"sessionid": locust.hxat_client.utm_source},
        name="/static",
        headers={
            "Accept": "text/css,*/*;q=0.1",
            "Referer": "{}/lti_init/launch_lti/".locust.host,
        },
        verify=locust.ssl_verify,
    )
    if response.status_code == requests.codes.ok:
        if response.content == "":
            response.failure("no data")
        else:
            response.success()
    else:
        response.failure("status code: {}".format(response.status_code))


def hxat_lti_launch(locust):
    target_path = "/lti_init/launch_lti/"
    consumer = ToolConsumer(
        consumer_key=locust.hxat_client.consumer_key,
        consumer_secret=locust.hxat_client.secret_key,
        launch_url="{}{}".format(locust.host, target_path),
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": locust.hxat_client.resource_link_id,
            "lis_person_sourcedid": locust.hxat_client.user_name,
            # lis_outcome_service_url sets graded assignment
            # "lis_outcome_service_url": os.environ.get('LIS_OUTCOME_SERVICE_URL', 'fake_url'),
            "user_id": locust.hxat_client.user_id,
            "roles": locust.hxat_client.user_roles,
            "context_id": locust.hxat_client.context_id,
            "context_title": locust.hxat_client.context_title,
            "custom_collection_id": locust.hxat_client.collection_id,
            "custom_object_id": locust.hxat_client.target_source_id,
        },
    )
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = consumer.generate_launch_data()
    response = locust.client.post(
        target_path,
        catch_response=True,
        name="/lti_launch/",
        headers=headers,
        data=params,
        verify=locust.ssl_verify,
    )

    if response.status_code == requests.codes.ok:
        if response.content == "":
            response.failure("no data")
            return False
        else:

            # locust.log('*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*..*')
            # locust.log(response.content)

            cookie_sid = response.cookies.get("sessionid", None)
            if not cookie_sid:
                response.failure("missing session-id cookies")
                return False
            else:
                locust.hxat_client.utm_source = cookie_sid
                response.success()
                return True
    else:
        response.failure("status code: {}".format(response.status_code))
        return False


def hxat_change_object(locust):
    # make sure to change to a different target_object
    ix = random.randint(
        0, len(COLLECTION_TARGET_DICT[locust.hxat_client.collection_id]) - 1
    )
    target_source_id = COLLECTION_TARGET_DICT[locust.hxat_client.collection_id][ix]
    # TARGET_DICT has to have more than 1 element, otherwise infinite loop!
    if len(COLLECTION_TARGET_DICT[locust.hxat_client.collection_id]) > 1:
        while target_source_id == locust.hxat_client.target_source_id:
            ix = random.randint(
                0, len(COLLECTION_TARGET_DICT[locust.hxat_client.collection_id]) - 1
            )
        target_source_id = COLLECTION_TARGET_DICT[locust.hxat_client.collection_id][ix]

    target_path = "/lti_init/admin_hub/{}/{}/{}/preview/?utm_source={}&resource_link_id={}".format(
        locust.hxat_client.context_id,
        locust.hxat_client.collection_id,
        target_source_id,
        locust.hxat_client.utm_source,
        locust.hxat_client.resource_link_id,
    )
    response = locust.client.get(
        target_path,
        catch_response=True,
        cookies={"sessionid": locust.hxat_client.utm_source},
        name="/page/{}".format(target_source_id),
        headers={
            "Accept": "text/css,*/*;q=0.1",
            "Referer": "{}/lti_init/launch_lti/".format(locust.host),
        },
        verify=locust.ssl_verify,
    )
    if response.status_code == requests.codes.ok:
        if response.content == "":
            response.failure("no data")
        else:
            response.success()

            # managing single ws connection
            if locust.ws_client is not None:
                locust.ws_client.close()
            # change object and ws reconnect
            locust.hxat_client.target_source_id = target_source_id
            try_reconnect(locust)
    else:
        response.failure("status code: {}".format(response.status_code))

    # search for annotations in new target-object
    hxat_search(locust)


def make_ws_app_url_path(locust):
    return "/ws/notification/{}--{}--{}".format(
        re.sub("[\W_]", "-", locust.hxat_client.context_id),
        re.sub("[\W_]", "-", locust.hxat_client.collection_id),
        locust.hxat_client.target_source_id,
    )


def create_ws_and_connect(locust):

    # check if ws client already exists for this locust client
    if locust.ws_client is None:
        # to create ws client, it has to have a successful lti-launch
        if locust.hxat_client.utm_source is not None:
            url_path = make_ws_app_url_path(locust)
            locust.log("-------------- URL_PATH={}".format(url_path))
            locust.ws_client = SocketClient(
                host=locust.host,
                hxat_utm_source=locust.hxat_client.utm_source,
                hxat_resource_link_id=locust.hxat_client.resource_link_id,
                app_url_path=url_path,
                verbose=locust.verbose,
                use_ssl=locust.use_ssl,
            )
        else:
            # unable to create ws before lti-launch
            events.request_failure.fire(
                request_type="ws",
                name="connection",
                response_time=None,
                response_length=0,
                exception=Exception("unable to create ws before lti-launch"),
            )
            return False

    # should have a ws_client
    locust.ws_client.connect(as_qs=True)


def try_reconnect(locust):
    if locust.ws_client.ws and locust.ws_client.ws.connected:
        pass
    else:
        locust.ws_client.app_url_path = make_ws_app_url_path(locust)
        locust.ws_client.connect(as_qs=True)
        if locust.ws_client.ws and locust.ws_client.ws.connected:
            locust.ws_client.log("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws RECONNECTED")
        else:
            locust.ws_client.log("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws reconnect FAILED")


# behavior
class WSJustConnect(TaskSet):
    wait_time = between(15, 90)

    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            # hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.css')
            # hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.js')
            # hxat_search(self.locust)
            create_ws_and_connect(self.locust)
        else:
            raise Exception("failed to lti login")

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()

    @task(1)
    def lurker(self):
        try_reconnect(self.locust)


class WSConnectAndDie(TaskSet):
    wait_time = between(15, 90)

    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            # hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.css')
            # hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.js')
            # hxat_search(self.locust)
            create_ws_and_connect(self.locust)
        else:
            raise Exception("failed to lti login")

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()

    @task(1)
    def wait_and_stop(self):
        self.locust.ws_client.log("************** about to close")
        self.locust.ws_client.close()
        time.sleep(2)
        self.locust.ws_client.log("************** about to reconnect")
        try_reconnect(self.locust)


class WSJustLTI(TaskSet):
    wait_time = between(15, 90)

    @task(1)
    def lurker(self):
        hxat_lti_launch(self.locust)


class WSConnectAndChangeObject(TaskSet):
    wait_time = between(15, 90)

    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            create_ws_and_connect(self.locust)
        else:
            raise Exception("failed to lti login")

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()

    @task(1)
    def change_object(self):
        hxat_change_object(self.locust)

    @task(10)
    def create_annotation(self):
        hxat_create(self.locust)

    @task(40)
    def search_annotation(self):
        hxat_search(self.locust)


class WSConnectAndCreate(TaskSet):
    wait_time = between(15, 90)

    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            create_ws_and_connect(self.locust)
        else:
            raise Exception("failed to lti login")

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()

    @task(10)
    def create_annotation(self):
        hxat_create(self.locust)

    @task(40)
    def search_annotation(self):
        hxat_search(self.locust)


"""
notes:
    to change to next target-object in the same assignment
    GET /lti_init/admin_hub/[context-id]/[collection-id]/[target-object-id]/preview/?utm_source=[sid]&resource_link_id=[resource-link-id]
"""
