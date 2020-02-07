
import code
import jwt
import sys

from datetime import datetime
from dateutil import tz
from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4

from locust import COLLECTION_ID
from locust import CONTEXT_ID
from locust import TARGET_SOURCE_ID
from locust import USER_ID


# this is particular to the target_source document
# how many text chars in a <p> element
target_doc = [0, 589, 313, 434, 593, 493]


# locust writest to stdout
class Console(code.InteractiveConsole):
    def write(self, data):
        #sys.stdout.write("\033[2K\033[E")
        #sys.stdout.write("\033[34m< " + data + "\033[39m")
        sys.stdout.write(data)
        sys.stdout.write("\n> ")
        sys.stdout.flush()

''' need to define these; want to be able to randomize at some point
from .utils import get_collection_id
from .utils import get_context_id
from .utils import get_context_title
from .utils import get_resource_link_id
from .utils import get_target_source_id
from .utils import get_user_id
from .utils import get_user_roles
from .utils import get_consumer_key
from .utils import get_secret_key
'''

#
# catchpy webannotation funcs
#
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
    ptag = randint(1, len(target_doc))
    sel_start = randint(0, target_doc[ptag])
    sel_end = randint(sel_start, target_doc[ptag])
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
            "can_admin": [USER_ID],
            "can_delete": [USER_ID],
            "can_read": [],
            "can_update": [USER_ID]
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
                        {"endSelector": {"type": "XPathSelector", "value": "/div[1]/p[{}]".format(ptag)},
                            "refinedBy": {"end": sel_end, "start": sel_start, "type": "TextPositionSelector"},
                            "startSelector": {"type": "XPathSelector", "value": "/div[1]/p[{}]".format(ptag)},
                            "type": "RangeSelector"},
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




