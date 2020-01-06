#!/usr/bin/env python3
# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

import time
import random
import hashlib
import os
import sys
import json
import argparse

from PIL import Image

from twisted.internet import reactor

from txzmq import ZmqEndpoint, ZmqEndpointType
from txzmq import ZmqFactory
from txzmq import ZmqSubConnection, ZmqPubConnection

sys.path.insert(1, os.path.realpath(os.path.pardir))

from onionstudio.pixel import Pixel
from onionstudio.png import PngToPixels
from onionstudio.extension import Extension


# This module publishes a script of messages to a ZMQ endpoint

PUBLISH_ENDPOINT = "tcp://127.0.0.1:5557"

HTLC_ACCEPTED_TAG = "htlc_accepted".encode("utf8")
FORWARD_EVENT_TAG = "forward_event".encode("utf8")

factory = ZmqFactory()

pub_endpoint = ZmqEndpoint(ZmqEndpointType.bind, PUBLISH_ENDPOINT)
pub_connection = ZmqPubConnection(factory, pub_endpoint)

MAX_X = 255
MAX_Y = 255

parser = argparse.ArgumentParser(prog="mock-tlv-png.py")
parser.add_argument("x_offset", type=int)
parser.add_argument("y_offset", type=int)
parser.add_argument("png_file", type=str)
s = parser.parse_args()

pp = PngToPixels(s.png_file)

pixels = list(pp.iter_at_offset(s.x_offset, s.y_offset))

def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]

TEST_PAYLOADS = []
for chunk in divide_chunks(pixels, 100):
    print("chunk: %s" % [str(p) for p in chunk])
    amount = (len(chunk) * 1000) + 1000
    forward_amount = 1000
    payload = Extension.encode_non_final(forward_amount, 100, "123x45x67",
                                         chunk)
    p = {'amount':         amount,
         'forward_amount': forward_amount,
         'payload':        payload.hex()}
    TEST_PAYLOADS.append(p)

def publish():
    print("starting to publish to %s" % PUBLISH_ENDPOINT)
    for p in TEST_PAYLOADS:
        payment_hash = os.urandom(32).hex()
        h = {"htlc":  {'amount':       "%dmsat" % p['amount'],
                       'payment_hash': payment_hash},
             "onion": {'forward_amount': "%dmsat" % p['forward_amount'],
                       'payload':        p['payload']},
            }
        msg = json.dumps(h).encode("utf8")
        print("publishing: %s" % msg)
        pub_connection.publish(msg, tag=HTLC_ACCEPTED_TAG)
        time.sleep(0.01)
        #if (random.random() < 0.5):
        #    continue
        m = {'forward_event': {'payment_hash': payment_hash,
                               'status':       "settled",
                               'fee':        p['amount'] - p['forward_amount']}}
        msg = json.dumps(m).encode("utf8")
        print("publishing: %s" % msg)
        pub_connection.publish(msg, tag=FORWARD_EVENT_TAG)
        time.sleep(0.01)
    reactor.stop()

reactor.callLater(1.0, publish)
reactor.run()
