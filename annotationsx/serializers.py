import json
from collections import OrderedDict


class JsonOrderedDictSerializer(object):
    """
    Simple wrapper around JSON serializer that decodes dicts as ordered dicts.
    """
    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':')).encode('latin-1')

    def loads(self, data):
        return json.loads(data.decode('latin-1'), object_pairs_hook=OrderedDict)