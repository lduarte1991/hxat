#
# ws heavily based on
# https://github.com/websocket-client/websocket-client/blob/master/bin/wsdump.py
#
import ast
import json
import os
import re
import ssl
import threading
from datetime import datetime, timedelta
from urllib.parse import urlparse
from uuid import uuid4

import iso8601
import websocket
from dateutil import tz
from locust import events
from utils import Console

# valid codes for ws read
OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)
# websocket.enableTrace(True)


class SocketClient(object):
    """hxat websockets client

    connects and reads from ws; does not send anything; ever.
    """

    def __init__(
        self,
        host,
        hxat_utm_source,
        hxat_resource_link_id,
        app_url_path="",
        timeout=2,
        verbose=False,
        use_ssl=True,
    ):
        self.console = Console()
        self.host = host
        self.hxat_utm_source = hxat_utm_source
        self.hxat_resource_link_id = hxat_resource_link_id
        self.ws_timeout = timeout
        self.verbose = verbose
        self.session_id = uuid4().hex
        self.protocol = "wss" if use_ssl else "ws"

        h = urlparse(self.host)
        self.hostname = h.netloc

        self.app_url_path = app_url_path

        self.ws = None
        self.thread = None

        events.quitting += self.on_close

    @property
    def url(self):
        return "{}://{}{}/".format(self.protocol, self.hostname, self.app_url_path)

    def log(self, msg):
        if self.verbose:
            self.console.write("[{}] {}".format(self.session_id, msg))

    def _prep_connection(self, as_qs=False, as_header=False, as_cookie=False):

        self.log(
            "-------------- PREP as_qs={} as_header={} as_cookie={}".format(
                as_qs, as_header, as_cookie
            )
        )

        if as_qs:
            conn_url = "{}?utm_source={}&resource_link_id={}".format(
                self.url, self.hxat_utm_source, self.hxat_resource_link_id
            )
        else:
            conn_url = self.url
        self.log("-------------- PREP TO CONN_URL={}".format(conn_url))

        header = (
            {
                "x_utm_source": self.hxat_utm_source,
                "x_lid_source": self.hxat_resource_link_id,
            }
            if as_header
            else {}
        )
        self.log("-------------- PREP HEADER={}".format(header))

        cookie = (
            {
                "sessionid": self.hxat_utm_source,
                "resourcelinkid": self.hxat_resource_link_id,
            }
            if as_cookie
            else {}
        )

        # TODO expects a string!
        cookie = "sessionid={}".format(self.hxat_utm_source) if as_cookie else ""
        self.log("-------------- CONNECT COOKIE={}".format(cookie))

        return (conn_url, header, cookie)

    def _get_connection(self, as_qs=False, as_header=False, as_cookie=False):
        if self.ws is not None:
            self.log("-------------- WEBSOCKET ws already exists")
            return self.ws

        self.log("-------------- WEBSOCKET must create ws connection")
        try:
            ws = websocket.WebSocket(
                sslopt={
                    "cert_reqs": ssl.CERT_NONE,  # do not check certs
                    "check_hostname": False,  # do not check hostname
                },
            )
        except Exception as e:
            self.log("-------------- WEBSOCKET exception [{}]: {}".format(e, e))
            return None
        else:
            self.log("-------------- WEBSOCKET SUCCESS")
            ws.settimeout = self.ws_timeout
            return ws

    def connect(self, as_qs=False, as_header=False, as_cookie=False):
        ws = self._get_connection(as_qs=as_qs, as_header=as_header, as_cookie=as_cookie)
        if ws is None:
            self.log("^-^-^-^-^-^-^- failed to get connection")
            return
        # have a ws object!
        self.ws = ws

        if self.ws.connected:
            self.log("nothing to do: already connected")
            # TODO: have to manage recv thread?
            return

        (conn_url, header, cookie) = self._prep_connection(
            as_qs=as_qs, as_header=as_header, as_cookie=as_cookie
        )
        try:
            self.ws.connect(
                url=conn_url, header=header, cookie=cookie,
            )
        except Exception as e:
            self.log(
                "^-^-^-^-^-^-^- CONNECT exception [{}]: {}".format(e, e)
            )  # response status_code == 403

            events.request_failure.fire(
                request_type="ws",
                name="connection",
                response_time=None,
                response_length=0,
                exception=e,
            )
            # client should be smarter and know that if 403, it probably will
            # not be able to connect, ever, due to wrong creds
        else:
            self.log("^-^-^-^-^-^-^- CONNECT SUCCESS")
            events.request_success.fire(
                request_type="ws",
                name="connection",
                response_time=None,
                response_length=0,
            )

            # if server closes the connection, the thread dies, but
            # if thread dies, it closes the connection?
            self.thread = threading.Thread(target=self.recv, daemon=True)
            self.thread.start()

    def close(self):
        if self.ws is not None:
            self.ws.close()
        else:
            self.log("nothing to do: NOT connected")

    def on_close(self):
        self.close()

    def _recv(self):
        try:
            frame = self.ws.recv_frame()
        except websocket.WebSocketException:
            return websocket.ABNF.OPCODE_CLOSE, None

        if not frame:
            return 0xB, None  # invented code for invalid frame
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
            # self.log('^^^^^^^^^^^^^^^^^^^^^^^^^ RECEIVE({})'.format(opcode))

            if opcode == websocket.ABNF.OPCODE_TEXT and isinstance(data, bytes):
                # success
                data = str(data, "utf-8")
                ws_msg = json.loads(data)
                weba = ast.literal_eval(ws_msg["message"])
                self.log("^^^^^^^^^^^^^^^^^^^^^^^^^ recv anno: {}".format(weba["id"]))
                created = iso8601.parse_date(weba["created"])
                ts_delta = (datetime.now(tz.tzutc()) - created) / (
                    timedelta(microseconds=1) * 1000
                )
                response_length = self.calc_response_length(data)
                events.request_success.fire(
                    request_type="ws",
                    name="receive",
                    response_time=ts_delta,
                    response_length=response_length,
                )

            elif opcode == websocket.ABNF.OPCODE_BINARY:
                # failure: don't understand binary
                events.request_failure.fire(
                    request_type="ws",
                    name="receive",
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException("Unexpected binary frame"),
                )

            elif opcode == 0xB:
                # failure: invalid frame
                events.request_failure.fire(
                    request_type="ws",
                    name="receive",
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException("Invalid frame"),
                )

            elif opcode == websocket.ABNF.OPCODE_CLOSE:
                self.log("^^^^^^^^^^^^^^^^^^^^^^^^^ recv CLOSE")
                break  # terminate loop

            elif opcode == websocket.ABNF.OPCODE_PING:
                # ignore ping-pong
                pass

            else:
                # failure: unknown
                events.request_failure.fire(
                    request_type="ws",
                    name="receive",
                    response_time=None,
                    response_length=0,
                    exception=websocket.WebSocketException(
                        "{}| Unknown error for opcode({})".format(
                            self.session_id, opcode
                        )
                    ),
                )

    def calc_response_length(self, response):
        json_data = json.dumps(response)
        return len(json_data)
