#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#
import os

from locust import between
from locust import HttpLocust
from locust import task
from locust import TaskSet

from .tasks import hxat_lti_launch
from .utils import Console
from .utils import get_collection_id
from .utils import get_context_id
from .utils import get_context_title
from .utils import get_resource_link_id
from .utils import get_target_source_id
from .utils import get_user_id
from .utils import get_user_roles
from .utils import get_consumer_key
from .utils import get_secret_key
from .utils import make_jwt
from .wsclient import SocketClient


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


class HxatLocust(HttpLocust):

    def __init__(self, *args, **kwargs):
        super(HxatLocust, self).__init__(*args, **kwargs)

        # log to stdout
        self.console = Console()

        # default is verbose=True
        self.verbose = os.environ.get('HXAT_LOCUST_VERBOSE', 'true').lower() == 'true'

        # settings for this hxat user instance
        self.hxat = dict()
        self.hxat['user_id'] = get_user_id()
        self.hxat['user_roles'] = get_user_roles()
        self.hxat['collection_id'] = get_collection_id()
        self.hxat['context_id'] = get_context_id()
        self.hxat['context_title'] = get_context_title()
        self.hxat['target_source_id'] = get_target_source_id()
        self.hxat['resource_link_id'] = get_resource_link_id()
        self.hxat['consumer_key'] = get_consumer_key()
        self.hxat['secret_key'] = get_secret_key()

        # TODO: this dumps lots of message for each http request
        self.ssl_verify = False


    def log(self, msg):
        # TODO: locust has a instance id?
        if self.verbose:
            self.console.write(msg)


class WSUserJustConnect(HttpLocust):
    weight = 3
    task_set = WSJustConnect

    def __init__(self, *args, **kwargs):
        super(WSUserJustConnect, self).__init__(*args, **kwargs)

        # log to stdout
        self.console = Console()

        # default is verbose=True
        self.verbose = os.environ.get('HXAT_LOCUST_VERBOSE', 'true').lower() == 'true'

        self.cookies = dict()  # csrf, session after lti-login
        self.store_token = make_jwt(
                apikey=os.environ.get('STORE_CONSUMER', 'fake_consumer'),
                secret=os.environ.get('STORE_SECRET', 'fake_secret'),
                user=get_user_id(),
                )

        # check if self-signed certs
        #if 'hxtech.org' in hostname:
        #    self.ssl_verify = os.environ.get('REQUESTS_CA_BUNDLE', False)
        #else:
        #    self.ssl_verify = True

    def log(self, msg):
        if self.verbose:
            self.console.write(msg)


