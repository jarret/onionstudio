#!/usr/bin/env python3
import time
import sys
import json
import argparse

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory

from txzmq import ZmqEndpoint, ZmqEndpointType
from txzmq import ZmqFactory
from txzmq import ZmqSubConnection

from bolt.util import h2b

from onionstudio.art_db import ArtDb
from onionstudio.compressor import compressor
from onionstudio.extension import Extension, PIXEL_TLV_TYPE


UNPAID_PRUNE_CHECK = 60
UNPAID_PRUNE_SECONDS = 120

###############################################################################

class AppClient(WebSocketServerProtocol):
    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket client connection open.")
        self.server.clients.append(self)
        art_bin = self.server.app.art_db.to_bin()
        compressed_bin = compressor(art_bin)
        print("compressed art bin len: %d" % len(compressed_bin))
        self.sendMessage(compressed_bin, isBinary=True)

    def onMessage(self, payload, isBinary):
        print("got message?")

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

###############################################################################

class AppServer(WebSocketServerFactory):
    def __init__(self, port, app):
        ws_url = u"ws://0.0.0.0:%d" % port
        super().__init__()
        self.setProtocolOptions(openHandshakeTimeout=15, autoPingInterval=30,
                                autoPingTimeout=5)

        self.protocol = AppClient
        self.protocol.server = self
        self.clients = []
        print("listening on websocket %s" % ws_url)
        reactor.listenTCP(port, self)
        self.app = app

    def echo_to_clients(self, pixels):
        pixels = [{'x': p.x, 'y': p.y, 'rgb': p.rgb} for p in pixels]
        message = {'pixels':   pixels}
        message = json.dumps(message)
        print("echoing to clients: %s" % message)
        for c in self.clients:
            c.sendMessage(message.encode("utf8"))

###############################################################################

HTLC_ACCEPTED_TAG = "htlc_accepted".encode("utf8")
FORWARD_EVENT_TAG = "forward_event".encode("utf8")

class App(object):
    def __init__(self, endpoint, mock_endpoint, port, art_db_dir):
        self.endpoint = endpoint
        self.mock_endpoint = mock_endpoint
        self.port = port
        self.art_db_dir = art_db_dir
        self.unpaid_htlcs = {}
        self.prune_loop = LoopingCall(self.prune_unpaid)
        self.prune_loop.start(interval=UNPAID_PRUNE_CHECK, now=False)

    ###########################################################################

    def setup_art_db(self):
        self.art_db = ArtDb(self.art_db_dir)

    ###########################################################################

    def setup_websocket(self):
        self.ws_server = AppServer(self.port, self)

    ###########################################################################

    def setup_zmq(self):
        zmq_factory = ZmqFactory()
        print("subscribing on: %s" % self.endpoint)
        sub_endpoint = ZmqEndpoint(ZmqEndpointType.connect, self.endpoint)
        sub_connection = ZmqSubConnection(zmq_factory, sub_endpoint)
        sub_connection.gotMessage = self.zmq_message
        sub_connection.subscribe(FORWARD_EVENT_TAG)
        sub_connection.subscribe(HTLC_ACCEPTED_TAG)

        print("subscribing on: %s" % self.mock_endpoint)
        sub_mock_endpoint = ZmqEndpoint(ZmqEndpointType.connect,
                                        self.mock_endpoint)
        sub_mock_connection = ZmqSubConnection(zmq_factory, sub_mock_endpoint)
        sub_mock_connection.gotMessage = self.zmq_message
        sub_mock_connection.subscribe(FORWARD_EVENT_TAG)
        sub_mock_connection.subscribe(HTLC_ACCEPTED_TAG)

    def forward_event_message(self, message):
        d = json.loads(message.decode('utf8'))['forward_event']
        print("got %s" % json.dumps(d, indent=1))

        if d['status'] != 'settled':
            print("invoice is not settled")
            return

        if d['payment_hash'] in self.unpaid_htlcs.keys():
            self.finish_htlc(d['payment_hash'])

    def htlc_accepted_message(self, message):
        d = json.loads(message.decode('utf8'))
        payment_hash = d['htlc']['payment_hash']
        amount = int(d['htlc']['amount'][:-4])
        forward_amount = int(d['onion']['forward_amount'][:-4])
        payload_hex = d['onion']['payload']
        payload = h2b(payload_hex)
        paid = amount - forward_amount
        parsed_payload, err = Extension.parse(payload)
        if err:
            print("could not parse payload: %s" % err)
            return
        print("parsed payload %s" % parsed_payload)
        pixels = parsed_payload['tlvs'][PIXEL_TLV_TYPE]['pixels']
        if (amount - forward_amount) < len(pixels) * 1000:
            print("forward fee not enough")
            return

        self.unpaid_htlcs[payment_hash] = {'payload_hex': payload_hex,
                                           'recv_time':   time.time()}

    def finish_htlc(self, payment_hash):
        payload_hex = self.unpaid_htlcs.pop(payment_hash)['payload_hex']
        payload = h2b(payload_hex)
        parsed_payload, err = Extension.parse(payload)
        assert err is None, "could not parse the second time?"
        pixels = parsed_payload['tlvs'][PIXEL_TLV_TYPE]['pixels']
        self.art_db.record_pixels(payload_hex, pixels)
        self.ws_server.echo_to_clients( pixels)

    def zmq_message(self, message, tag):
        if tag == FORWARD_EVENT_TAG:
            self.forward_event_message(message)
        elif tag == HTLC_ACCEPTED_TAG:
            self.htlc_accepted_message(message)
        else:
            sys.exit("unknown tag: %s" % tag)

    ###########################################################################

    def prune_unpaid(self):
        now = time.time()
        new = {k: v for k, v in self.unpaid_htlcs.items() if
               (now - v['recv_time']) < UNPAID_PRUNE_SECONDS}
        #print("pruning: %d to %d" % (len(self.unpaid_htlcs), len(new)))
        self.unpaid_htlcs = new

    ###########################################################################

    def run(self):
        self.setup_websocket()
        self.setup_zmq()
        self.setup_art_db()

    def stop(self):
        self.art_db.unmap_art_bin()


###############################################################################

DEFAULT_WEBSOCKET_PORT = 9000

DEFAULT_ZMQ_SUBSCRIBE_ENDPOINT = "tcp://127.0.0.1:6666"
DEFAULT_MOCK_ZMQ_SUBSCRIBE_ENDPOINT = "tcp://127.0.0.1:5557"

DEFAULT_ART_DB_DIR = "/tmp/onionstudio/"

parser = argparse.ArgumentParser(prog="onionstudio.py")
parser.add_argument("-e", "--endpoint", type=str,
                    default=DEFAULT_ZMQ_SUBSCRIBE_ENDPOINT,
                    help="endpoint to subscribe to for zmq notifications from "
                          "c-lightning via cl-zmq.py plugin")
parser.add_argument("-m", "--mock-endpoint", type=str,
                    default=DEFAULT_MOCK_ZMQ_SUBSCRIBE_ENDPOINT,
                    help="endpoint to subscribe to zmq notifcations from a "
                         "test script such as mock-png.py")
parser.add_argument("-w", "--websocket-port", type=int,
                    default=DEFAULT_WEBSOCKET_PORT,
                    help="port to listen for incoming websocket connections")
parser.add_argument("-a", "--art-db-dir", type=str, default=DEFAULT_ART_DB_DIR,
                    help="directory to save the image state and logs")
settings = parser.parse_args()

a = App(settings.endpoint, settings.mock_endpoint, settings.websocket_port,
        settings.art_db_dir)
a.run()


reactor.addSystemEventTrigger("before", "shutdown", a.stop)

reactor.run()
