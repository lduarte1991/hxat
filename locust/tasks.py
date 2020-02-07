
import json
import os

from lti import ToolConsumer
from uuid import uuid4

from .locust import COLLECTION_ID
from .locust import CONTEXT_ID
from .locust import RESOURCE_LINK_ID
from .locust import TARGET_SOURCE_ID
from .locust import USER_ID
from .utils import fresh_wa


def hxat_create(locust):
    catcha = fresh_wa()

    anno_id = str(uuid4())
    params = {
            'resource_link_id': locust.hxat['resource_link_id'],
            'utm_source': locust.hxat['utm_source'],
            'version': 'catchpy',
            }
    target_path = '/annotation_store/api/{}?'.format(anno_id)
    response = locust.client.post(
        target_path, json=catcha, catch_response=True,
        name='/annotation_store/api/create',
        headers={
            'Content-Type': 'Application/json',
            'x-annotator-auth-token': locust.store_token,
            'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
        },
        params=params,
        verify=locust.ssl_verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        try:
            a_id = response.json()['id']
        except KeyError:
            resp = response.json()
            if 'payload' in resp:
                response.failure(resp['payload'])
            else:
                response.failure('no id in response')
            return
        except json.decoder.JSONDecodeError as e:
            response.failure(e)
            return
        else:
            response.success()


def hxat_search(locust, limit=50, offset=0):
    params = {
        'resource_link_id': locust.hxat['resource_link_id'],
        'utm_source': locust.hxat['utm_source'],
        'version': 'catchpy',
        'limit': limit,
        'offset': offset,
        'media': 'text',
        'source_id': locust.hxat['target_source_id'],
        'context_id': locust.hxat['context_id'],
        'collection_id': locust.hxat['collection_id'],
    }
    target_path = '/annotation_store/api/'
    response = locust.client.get(
            target_path, catch_response=True,
            name='/annotation_store/api/search',
            headers={
                'Content-Type': 'Application/json',
                'x-annotator-auth-token': locust.store_token,
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            params=params,
            verify=locust.ssl_verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        try:
            rows = response.json()['rows']
        except KeyError:
            resp = response.json()
            if 'payload' in resp:
                response.failure(resp['payload'])
            else:
                response.failure('missing rows in search response')
            return
        except json.decoder.JSONDecodeError as e:
            response.failure(e)
            return
        else:
            response.success()


def hxat_get_static(locust, url_path):
    target_path = os.path.join('/static/', url_path)
    response = locust.client.get(
            target_path, catch_response=True,
            cookies={'sessionid': locust.hxat['utm_source']},
            name='/static',
            headers={
                'Accept': 'text/css,*/*;q=0.1',
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            verify=locust.ssl_verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        response.success()


def hxat_lti_launch(locust):
    target_path = '/lti_init/launch_lti/'
    consumer = ToolConsumer(
            consumer_key=locust.hxat['consumer_key']
            consumer_secret=locust.hxat['secret_key']
            launch_url='{}{}'.format(locust.host, target_path),
            params={
                "lti_message_type": "basic-lti-launch-request",
                "lti_version": "LTI-1p0",
                "resource_link_id": locust.hxat['resource_link_id'],
                # TODO check if lis_* actually needed for hxat
                #"lis_person_sourcedid": locust.hxat['user_name'],
                #"lis_outcome_service_url": os.environ.get('LIS_OUTCOME_SERVICE_URL', 'fake_url'),
                "user_id": locust.hxat['user_id'],
                "roles": locust.hxat{'user_roles'],
                "context_id": locust.hxat['context_id'],
                "context_title": locust.hxat['context_title'],
                },
            )
    headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            }
    params = consumer.generate_launch_data()
    response = locust.client.post(
            target_path, catch_response=True,
            name='/lti_launch/', headers=headers, data=params,
            verify=locust.ssl_verify,
            )
    if response.content == '':
        response.failure('no data')
    else:
        cookie_sid = response.cookies.get('sessionid', None)
        if not cookie_sid:
            response.failure('missing session-id cookies')
            return False
        else:
            locust.hxat['utm_source'] = cookie_sid
            response.success()
            return True


def create_ws_and_connect(locust):
    pass

def try_reconnect(locust):
    if locust.ws_client.ws and locust.ws_client.ws.connected:
        pass
    else:
        locust.ws_client.connect()
        if locust.ws_client.ws and locust.ws_client.ws.connected:
            locust.ws_client.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws RECONNECTED')
        else:
            locust.ws_client.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws reconnect FAILED')


class WSJustConnect(TaskSet):
    wait_time = between(15, 90)

    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            #hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.css')
            #hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.js')
            #hxat_search(self.locust)
            self.locust.ws_client.connect()
        else:
            raise Exception('failed to lti login')

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()


    @task(1)
    def lurker(self):
        try_reconnect(self.locust)


