import jwt
import os

from datetime import datetime
from dateutil import tz
from uuid import uuid4

from locust import HttpLocust

from utils import Console


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
            utm_source=None,
            ):
        self.user_id = user_id
        self.user_name = user_name
        self.user_roles = user_roles
        self.collection_id = collection_id
        self.context_id = context_id
        self.context_title = context_title
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



FAKE_USER_ID = 'fake_user'
FAKE_USER_NAME = 'fake_username'
FAKE_USER_ROLES = 'Learner'
FAKE_COLLECTION_ID = 'fake-collection-id'
FAKE_CONTEXT_ID = 'fake-context-id'
FAKE_CONTEXT_TITLE = 'fake-context-id-title'
FAKE_TARGET_SOURCE_ID = '0'
FAKE_RESOURCE_LINK_ID = 'fake-resource-link-id'
FAKE_HXAT_CONSUMER = 'fake-consumer-key'
FAKE_HXAT_SECRET = 'fake-secret-key'
FAKE_STORE_CONSUMER = 'fake-store-consumer'
FAKE_STORE_SECRET = 'fake-store-secret'


def get_hxat_client(cat='fake'):
    if cat == 'from_env':
        return HxatClient(
                user_id=os.environ.get('USER_ID', FAKE_USER_ID),
                user_name=os.environ.get('USER_NAME', FAKE_USER_NAME),
                user_roles=[r.strip() for r in  \
                        os.environ.get('USER_ROLES', FAKE_USER_ROLES).split(',')],
                collection_id=os.environ.get('COLLECTION_ID', FAKE_COLLECTION_ID),
                context_id=os.environ.get('CONTEXT_ID', FAKE_CONTEXT_ID),
                context_title=os.environ.get('CONTEXT_TITLE', FAKE_CONTEXT_TITLE),
                target_source_id=os.environ.get('TARGET_SOURCE_ID', FAKE_TARGET_SOURCE_ID),
                resource_link_id=os.environ.get('RESOURCE_LINK_ID', FAKE_RESOURCE_LINK_ID),
                consumer_key=os.environ.get('HXAT_CONSUMER', FAKE_HXAT_CONSUMER),
                secret_key=os.environ.get('HXAT_SECRET', FAKE_HXAT_SECRET),
                store_consumer=os.environ.get('STORE_CONSUMER', FAKE_STORE_CONSUMER),
                store_secret=os.environ.get('STORE_SECRET', FAKE_STORE_SECRET),
        )
    else:
        return HxatClient(
                user_id=FAKE_USER_ID,
                user_name=FAKE_USER_NAME,
                user_roles=[r.strip() for r in FAKE_USER_ROLES.split(',')],
                collection_id=FAKE_COLLECTION_ID,
                context_id=FAKE_CONTEXT_ID,
                context_title=FAKE_CONTEXT_TITLE,
                target_source_id=FAKE_TARGET_SOURCE_ID,
                resource_link_id=FAKE_RESOURCE_LINK_ID,
                consumer_key=FAKE_HXAT_CONSUMER,
                secret_key=FAKE_HXAT_SECRET,
                store_consumer=FAKE_STORE_CONSUMER,
                store_secret=FAKE_STORE_SECRET,
        )



# locust client
class HxatLocust(HttpLocust):

    def __init__(self, *args, **kwargs):
        super(HxatLocust, self).__init__(*args, **kwargs)

        # log to stdout
        self.console = Console()

        # default is verbose=True
        self.verbose = os.environ.get('HXAT_LOCUST_VERBOSE', 'true').lower() == 'true'

        # settings for this hxat user instance
        self.hxat_client = get_hxat_client(cat='from_env')

        # TODO: this dumps lots of message for each http request
        self.ssl_verify = False

        # check if should use ssl (for ws)
        self.use_ssl = self.host.startswith('https')

        # do not create ws-client until a successful lti-launch
        self.ws_client = None

        for attr, value in vars(self.hxat_client).items():
            self.console.write('----- {} = {} '.format(attr, value))


    def log(self, msg):
        # TODO: locust has a instance id?
        if self.verbose:
            self.console.write(msg)

