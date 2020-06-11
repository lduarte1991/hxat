
import code
import sys

from random import randint
from subprocess import Popen
from subprocess import PIPE
from uuid import uuid4


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


#
# catchpy webannotation funcs
#
def fetch_fortune():
    process = Popen('fortune', shell=True, stdout=PIPE, stderr=None)
    output, _ = process.communicate()
    return output.decode('utf-8')


def fresh_ann(hxat_client):
    ptag = randint(1, (len(target_doc)-1))
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
            "id": hxat_client.user_id,
            "name": hxat_client.user_name,
        },
        "id": str(uuid4()),
        "permissions": {
            "can_admin": [hxat_client.user_id],
            "can_delete": [hxat_client.user_id],
            "can_read": [],
            "can_update": [hxat_client.user_id]
        },
        "platform": {
            "collection_id": hxat_client.collection_id,
            "context_id": hxat_client.context_id,
            "platform_name": "edX",
            "target_source_id": hxat_client.target_source_id,
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


