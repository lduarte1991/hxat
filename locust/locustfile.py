#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#

from hxat_client import HxatLocust
from tasks import WSJustConnect


class WSUserJustConnect(HxatLocust):
    weight = 3
    task_set = WSJustConnect



