import code
import jwt
import os
import sys

from datetime import datetime
from dateutil import tz
from uuid import uuid4

from locust import HttpLocust


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


class HxatClient(object):

    def __init__(
            self,
            user_id,
            user_name,
            user_roles,
            collection_id,
            context_id,
            context_title,
            target_source_id,
            resource_link_id,
            consumer_key,
            secret_key,
            store_consumer,
            store_secret,
            utm_source,
            ):
        self.user_id = user_id
        self.user_name = user_name
        self.user_roles = user_roles
        self.collection_id = collection_id
        self.context_id = context_id
        self.target_source_id = target_source_id
        self.resource_link_id = resource_link_id
        self.consumer_key = consumer_key
        self.secret_key = secret_key
        self.store_consumer = store_consumer
        self.store_secret = store_secret
        self.utm_source = utm_source


    @property
    def store_token(self):
        return make_jwt(
                apikey=self.store_consumer,
                secret=self.store_secret,
                user=self.user_id
                )


def get_hxat_client(cat='fake'):
    if cat == 'fake':
        return HxatClient(
                user_id='fake_user',
                user_name='fake_username',
                user_roles='Learner',
                collection_id='fake-collection-id',
                context_id='fake-context-id',
                context_title='fake-context-id-title',
                target_source_id='0',
                resource_link_id='fake-resource-link-id',
                consumer_key='fake-consumer-key',
                secret_key='fake-secret-key',
                store_consumer='fake-store-consumer',
                store_secret='fake-store-secret',
                utm_source='fake_utm_source',
                )


# locust writest to stdout
class Console(code.InteractiveConsole):
    def write(self, data):
        #sys.stdout.write("\033[2K\033[E")
        #sys.stdout.write("\033[34m< " + data + "\033[39m")
        sys.stdout.write(data)
        sys.stdout.write("\n> ")
        sys.stdout.flush()


# locust client
class HxatLocust(HttpLocust):

    def __init__(self, *args, **kwargs):
        super(HxatLocust, self).__init__(*args, **kwargs)

        # log to stdout
        self.console = Console()

        # default is verbose=True
        self.verbose = os.environ.get('HXAT_LOCUST_VERBOSE', 'true').lower() == 'true'

        # settings for this hxat user instance
        self.hxat_client = get_hxat_client()

        # TODO: this dumps lots of message for each http request
        self.ssl_verify = False


    def log(self, msg):
        # TODO: locust has a instance id?
        if self.verbose:
            self.console.write(msg)

