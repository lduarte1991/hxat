#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#

from hxat_client import HxatLocust
from tasks import WSJustConnect
from tasks import WSJustLTI


class WSUserJustConnect(HxatLocust):
    weight = 3
    task_set = WSJustConnect


#class WSUserJustLTI(HxatLocust):
#    weight = 3
#    task_set = WSJustLTI


