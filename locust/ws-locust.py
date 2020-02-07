#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#
import code
import gevent
import iso8601
import json
import jwt
import os
import re
import ssl
import sys
import threading
import time

from datetime import datetime
from datetime import timedelta
from dateutil import tz
from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4

from locust import between
from locust import constant
from locust import events
from locust import HttpLocust
from locust import Locust
from locust import seq_task
from locust import task
from locust import TaskSequence
from locust import TaskSet
from locust import ResponseError
from lti import ToolConsumer

import websocket


#info from environment
#---------------------
USER_ID = os.environ.get('USER_ID', 'fake_user_id')
USER_NAME = os.environ.get('USER_NAME', 'fake_user_name')
CONTEXT_ID = os.environ.get('CONTEXT_ID', 'fake_context_id')
COLLECTION_ID = os.environ.get('COLLECTION_ID', 'fake_collection_id')
TARGET_SOURCE_ID = os.environ.get('TARGET_SOURCE_ID', '0')
RESOURCE_LINK_ID = os.environ.get('RESOURCE_LINK_ID', 'fake_resource_link_id')

VERBOSE = os.environ.get('WS_TEST_VERBOSE', 'true').lower() == 'true'

# this is particular to the target_source document
# and used to randomize the region being annotate
PTAG=2
target_doc = [0, 589, 313, 434, 593, 493]

# valid codes for ws read
OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)
#websocket.enableTrace(True)

class Console(code.InteractiveConsole):
    def write(self, data):
        sys.stdout.write("\033[2K\033[E")
        sys.stdout.write("\033[34m< " + data + "\033[39m")
        sys.stdout.write("\n> ")
        sys.stdout.flush()


class SocketClient(object):
    '''hxat websockets client

    connects and reads from ws; does not send anything; ever.
    '''
    def __init__(self, host, app_url_path='', timeout=2):
        self.console = Console()
        self.verbose = VERBOSE
        self.host = host
        self.session_id = uuid4().hex
        #self.protocol = 'wss'
        self.protocol = 'ws'
        path = os.path.join('/', app_url_path)
        self.url = '{}://{}{}/'.format(self.protocol, host, path)
        self.ws = None
        self.ws_timeout = timeout
        self.thread = None
        self.session_id = None

        events.quitting += self.on_close

    def log(self, msg):
        if self.verbose:
            self.console.write('[{}] {}'.format(self.session_id, msg))


    def connect(self):
        if self.ws is None:
            try:
                if self.session_id:
                    session_url = '{}?utm_source={}'.format(self.url, self.session_id)
                else:
                    session_url = self.url

                self.log('-------------- CONNECT TO URL={}'.format(self.url))
                self.log('-------------- CONNECT TO SESSION_URL={}'.format(session_url))
                self.log('-------------- CONNECT TO HOST={}'.format(self.host))

                self.ws = websocket.create_connection(
                        url=session_url,
                        sslopt={
                            'cert_reqs': ssl.CERT_NONE,  # do not check certs
                            'check_hostname': False,     # do not check hostname
                            }
                        )
            except Exception as e:
                events.request_failure.fire(
                    request_type='ws-conn', name='connection',
                    response_time=None,
                    response_length=0,
                    exception=e,
                    )
            else:
                events.request_success.fire(
                    request_type='ws-conn', name='connection',
                    response_time=None,
                    response_length=0)


                # if server closes the connection, the thread dies, but
                # if thread dies, it closes the connection?
                self.thread = threading.Thread(
                        target=self.recv,
                        daemon=True
                        )
                self.thread.start()
        else:
            self.log('nothing to do: already connected')


    def close(self):
        if self.ws is not None:
            self.ws.close()
        else:
            self.log('nothing to do: NOT connected')

    def on_close(self):
        self.close()


    def _recv(self):
        try:
            frame = self.ws.recv_frame()
        except websocket.WebSocketException:
            return websocket.ABNF.OPCODE_CLOSE, None

        if not frame:
            return 0xb, None  # invented code for invalid frame
        elif frame.opcode in OPCODE_DATA:
            return frame.opcode, frame.data
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            # server closed ws connection
            self.ws.send_close()
            return frame.opcode, None
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            self.ws.pong(frame.data)
            return frame.opcode, frame.data

        return frame.opcode, frame.data


    def recv(self):
        while True:
            opcode, data = self._recv()

            if opcode == websocket.ABNF.OPCODE_TEXT and isinstance(
                    data, bytes):
                # success
                data = str(data, 'utf-8')
                weba = json.loads(data)
                self.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ recv anno_id: {}'.format(weba['message']['id']))
                created = iso8601.parse_date(weba['message']['created'])
                ts_delta = (datetime.now(tz.tzutc()) - \
                        created) / (timedelta(microseconds=1) * 1000)
                response_length = self.calc_response_length(data)
                events.request_success.fire(
                    request_type='ws-recv', name='receive',
                    response_time=ts_delta,
                    response_length=response_length)

            elif opcode == websocket.ABNF.OPCODE_BINARY:
                # failure: don't understand binary
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException(
                        'Unexpected binary frame'),
                    )

            elif opcode == 0xb:
                # failure: invalid frame
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException(
                        'Invalid frame'),
                    )

            elif opcode == websocket.ABNF.OPCODE_CLOSE:
                self.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ recv CLOSE')
                break  # terminate loop

            elif opcode == websocket.ABNF.OPCODE_PING:
                # ignore ping-pong
                pass

            else:
                # failure: unknown
                events.request_failure.fire(
                    request_type='ws-recv', name='receive',
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException(
                        '{}| Unknown error for opcode({})'.format(
                            self.session_id, opcode)),
                    )



    def calc_response_length(self, response):
        length = 0
        json_data = json.dumps(response)
        return len(json_data)


######################################################
# http hxat operations:
#   lti login
#   get static pages (hxighlighter javascripts and css)
#   search annotations
#   create annotation
######################################################

def make_jwt(
    apikey, secret, user,
    iat=None, ttl=36000, override=[],
    backcompat=False):
    payload = {
        'consumerKey': apikey if apikey else str(uuid4()),
        'userId': user if user else str(uuid4()),
        'issuedAt': iat if iat else datetime.now(tz.tzutc()).isoformat(),
        'ttl': ttl,
    }
    if not backcompat:
        payload['override'] = override

    return jwt.encode(payload, secret)


def fetch_fortune():
    process = Popen('fortune', shell=True, stdout=PIPE, stderr=None)
    output, _ = process.communicate()
    return output.decode('utf-8')

def fresh_wa():
    sel_start = randint(0, target_doc[PTAG])
    sel_end = randint(sel_start, target_doc[PTAG])
    x = {
        "@context": "http://catchpy.harvardx.harvard.edu.s3.amazonaws.com/jsonld/catch_context_jsonld.json",
        "body": {
            "type": "List",
            "items": [{
                "format": "text/html",
                "language": "en",
                "purpose": "commenting",
                "type": "TextualBody",
                "value": fetch_fortune()
            }],
        },
        "creator": {
            "id": "d99019cf42efda58f412e711d97beebe",
            "name": "nmaekawa2017"
        },
        "id": "013ec74f-1234-5678-3c61-b5cf9d6f7484",
        "permissions": {
            "can_admin": [ USER_ID ],
            "can_delete": [ USER_ID ],
            "can_read": [],
            "can_update": [ USER_ID ]
        },
        "platform": {
            "collection_id": COLLECTION_ID,
            "context_id": CONTEXT_ID,
            "platform_name": "edX",
            "target_source_id": TARGET_SOURCE_ID,
        },
        "schema_version": "1.1.0",
        "target": {
            "items": [{
                "selector": {
                    "items": [
                        { "endSelector": { "type": "XPathSelector", "value": "/div[1]/p[{}]".format(PTAG) },
                            "refinedBy": { "end": sel_end, "start": sel_start, "type": "TextPositionSelector" },
                            "startSelector": { "type": "XPathSelector", "value": "/div[1]/p[{}]".format(PTAG) },
                            "type": "RangeSelector" },
                    ],
                    "type": "Choice"
                },
                "source": "http://sample.com/fake_content/preview", "type": "Text"
            }],
            "type": "List"
        },
        "type": "Annotation"
    }
    return x

def hxat_create(locust):
    catcha = fresh_wa()

    # create annotation
    anno_id = str(uuid4())
    params = {
            'resource_link_id': RESOURCE_LINK_ID,
            'utm_source': locust.cookies['UTM_SOURCE'],
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
        verify=locust.verify,
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
            'resource_link_id': RESOURCE_LINK_ID,
            'utm_source': locust.cookies['UTM_SOURCE'],
            'version': 'catchpy',
            'limit': limit,
            'offset': offset,
            'media': 'text',
            'source_id': TARGET_SOURCE_ID,
            'context_id': CONTEXT_ID,
            'collection_id': COLLECTION_ID,
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
            verify=locust.verify,
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
            cookies=locust.cookies,
            name='/static',
            headers={
                'Accept': 'text/css,*/*;q=0.1',
                'Referer': 'https://naomi.hxat.hxtech.org/lti_init/launch_lti/',
            },
            verify=locust.verify,
    )
    if response.content == '':
        response.failure('no data')
    else:
        response.success()


def hxat_lti_launch(locust):

    target_path = '/lti_init/launch_lti/'
    consumer = ToolConsumer(
            consumer_key=os.environ.get('HXAT_CONSUMER', 'fake_consumer_key'),
            consumer_secret=os.environ.get('HXAT_SECRET', 'fake_secret_key'),
            launch_url='{}{}'.format(locust.host, target_path),
            params={
                "lti_message_type": "basic-lti-launch-request",
                "lti_version": "LTI-1p0",
                "resource_link_id": RESOURCE_LINK_ID,
                "lis_person_sourcedid": os.environ.get('LIS_PERSON_SOURCEDID','fake_person'),
                "lis_outcome_service_url": os.environ.get('LIS_OUTCOME_SERVICE_URL', 'fake_url'),
                "user_id": USER_ID,
                "roles": os.environ.get('USER_ROLES', 'Administrator'),
                "context_id": CONTEXT_ID,
                "context_title": '{}-title'.format(CONTEXT_ID),
                },
            )
    headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            }
    params = consumer.generate_launch_data()
    response = locust.client.post(
            target_path, catch_response=True,
            name='/lti_launch/', headers=headers, data=params,
            verify=locust.verify,
            )
    if response.content == '':
        response.failure('no data')
    else:
        cookie_sid = response.cookies.get('sessionid', None)
        if not cookie_sid:
            response.failure('missing session-id cookies')
            return False
        else:
            locust.cookies['UTM_SOURCE'] = cookie_sid
            locust.ws_client.session_id = cookie_sid
            response.success()
            return True


def try_reconnect(locust):
    if locust.ws_client.ws and locust.ws_client.ws.connected:
        pass
    else:
        locust.ws_client.connect()
        if locust.ws_client.ws and locust.ws_client.ws.connected:
            locust.ws_client.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws RECONNECTED')
        else:
            locust.ws_client.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws reconnect FAILED')



class WSBehavior15_90(TaskSet):
    #wait_time = between(15, 90)
    wait_time = between(90, 300)
    def on_start(self):
        # basic lti login for hxat text annotation
        ret = hxat_lti_launch(self.locust)
        if ret:
            hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.css')
            hxat_get_static(self.locust, '/Hxighlighter/hxighlighter_text.js')
            hxat_search(self.locust)
            self.locust.ws_client.connect()
            if self.locust.ws_client.ws and self.locust.ws_client.ws.connected:
                self.locust.ws_client.log('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ws CONNECTED')
        else:
            raise Exception('failed to lti login')

    def on_stop(self):
        if self.locust.ws_client is not None:
            self.locust.ws_client.close()


    @task(2)
    def lurker1(self):
        try_reconnect(self.locust)
        hxat_search(
                locust=self.locust,
                limit=randint(10, 50),
                offset=randint(50, 200),
                )

    @task(10)
    def lurker2(self):
        try_reconnect(self.locust)
        hxat_search(
                locust=self.locust,
                )

    @task(1)
    def homework1(self):
        try_reconnect(self.locust)
        hxat_create(self.locust)
        hxat_search(self.locust)



class WSJustConnect(TaskSet):
    #wait_time = between(15, 90)
    wait_time = constant(15)

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




class WSUser15_90(HttpLocust):
    weight = 1
    task_set = WSBehavior15_90

    def __init__(self, *args, **kwargs):
        super(WSUser15_90, self).__init__(*args, **kwargs)

        self.console = Console()
        #self.verbose = VERBOSE
        self.cookies = dict()  # csrf, session after lti-login
        self.store_token = make_jwt(
                apikey=os.environ.get('STORE_CONSUMER', 'fake_consumer'),
                secret=os.environ.get('STORE_SECRET', 'fake_secret'),
                user=USER_ID
                )
        # remove protocol from url so we can do wss requests
        (proto, hostname) = self.host.split('//')
        url_path = '/ws/notification/{}--{}--{}'.format(
                re.sub('[\W_]', '-', CONTEXT_ID),
                re.sub('[\W_]', '-', COLLECTION_ID),
                TARGET_SOURCE_ID
                )
        self.ws_client = SocketClient(hostname, app_url_path=url_path)

        # check if self-signed certs
        if 'hxtech.org' in hostname:
            self.verify = os.environ.get('REQUESTS_CA_BUNDLE', False)
        else:
            self.verify = True

    def log(self, msg):
        if self.verbose:
            self.console.write(msg)

class WSUserJustConnect(HttpLocust):
    weight = 3
    task_set = WSJustConnect

    def __init__(self, *args, **kwargs):
        super(WSUserJustConnect, self).__init__(*args, **kwargs)

        self.console = Console()
        #self.verbose = VERBOSE
        self.cookies = dict()  # csrf, session after lti-login
        self.store_token = make_jwt(
                apikey=os.environ.get('STORE_CONSUMER', 'fake_consumer'),
                secret=os.environ.get('STORE_SECRET', 'fake_secret'),
                user=USER_ID
                )
        # remove protocol from url so we can do wss requests
        (proto, hostname) = self.host.split('//')
        url_path = '/ws/notification/{}--{}--{}'.format(
                re.sub('[\W_]', '-', CONTEXT_ID),
                re.sub('[\W_]', '-', COLLECTION_ID),
                TARGET_SOURCE_ID
                )
        print('-------------- URL_PATH={}'.format(url_path))
        self.ws_client = SocketClient(hostname, app_url_path=url_path)

        # check if self-signed certs
        if 'hxtech.org' in hostname:
            self.verify = os.environ.get('REQUESTS_CA_BUNDLE', False)
        else:
            self.verify = True

    def log(self, msg):
        if self.verbose:
            self.console.write(msg)

