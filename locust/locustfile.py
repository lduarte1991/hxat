#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#

from hxat_client import HxatLocust
from tasks import WSConnectAndChangeObject
from tasks import WSConnectAndDie
from tasks import WSJustConnect
from tasks import WSJustLTI


# class WSUserConnectAndDie(HxatLocust):
#    weight = 3
#    task_set = WSConnectAndDie


# class WSUserJustConnect(HxatLocust):
#    weight = 3
#    task_set = WSJustConnect


# class WSUserJustLTI(HxatLocust):
#    weight = 3
#    task_set = WSJustLTI


class WSUserConnectAndChangeObject(HxatLocust):
    weight = 3
    task_set = WSConnectAndChangeObject
