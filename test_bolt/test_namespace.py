#!/usr/bin/env python3
# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import os
import sys
import random
import json

sys.path.insert(1, os.path.realpath(os.path.pardir))

from bolt.util import h2b
from bolt.namespace import Namespace

# test namespaces as defined by:
# https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#appendix-b-type-length-value-test-vectors

class TestNamespace1:
    def parse_tlv1(self, tlv):
        print("parsing tlv1: %s" % tlv)
        amount_msat, remainder, err = Namespace.pop_tu64(tlv.l, tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name':   "tlv1",
                'amount_msat':     amount_msat}, None

    def parse_tlv2(self, tlv):
        print("parsing tlv2: %s" % tlv)
        short_channel_id, remainder, err = Namespace.pop_short_channel_id(tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name':    "tlv2",
                'short_channel_id': short_channel_id}, None

    def parse_tlv3(self, tlv):
        print("parsing tlv3: %s" % tlv)
        node_id, remainder, err = Namespace.pop_point(tlv.v)
        if err:
            return None, err
        amount_msat_1, remainder, err = Namespace.pop_u64(remainder)
        if err:
            return None, err
        amount_msat_2, remainder, err = Namespace.pop_u64(remainder)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name': "tlv3",
                'node_id':       node_id,
                'amount_msat_1': amount_msat_1,
                'amount_msat_2': amount_msat_2}, None

    def parse_tlv4(self, tlv):
        print("parsing tlv4: %s" % tlv)
        cltv_delta, remainder, err = Namespace.pop_u16(tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name': "tlv4",
                'cltv_delta':    cltv_delta}, None

    def parse(self, byte_string):
        tlv_parsers = {1:   self.parse_tlv1,
                       2:   self.parse_tlv2,
                       3:   self.parse_tlv3,
                       254: self.parse_tlv4}
        return Namespace.parse(byte_string, tlv_parsers)


class TestNamespace2:
    def parse_tlv1(self, tlv):
        amount_msat, remainder, err = Namespace.pop_tu64(tlv.l, tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name': "tlv1",
                'amount_msat':   amount_msat}, None

    def parse_tlv2(self, tlv):
        cltv_expiry, remainder, err = Namespace.pop_tu32(tlv.l, tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name': "tlv2",
                'cltv_expiry':   cltv_expiry}, None

    def parse(self, byte_string):
        tlv_parsers = {0:  self.parse_tlv1,
                       11: self.parse_tlv2}
        return Namespace.parse(byte_string, tlv_parsers)



# from: https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#tlv-decoding-failures

TEST_BOTH_NAMESPACES_INVALID = [
    "1200",
    "fd010200",
    "fe0100000200",
    "ff010000000000000200",
]

# from: https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#tlv-decoding-failures
TEST_NAMESPACE1_INVALID = [
    "0109ffffffffffffffffff",
    "010100",
    "01020001",
    "0103000100",
    "010400010000",
    "01050001000000",
    "0106000100000000",
    "010700010000000000",
    "01080001000000000000",
    "020701010101010101",
    "0209010101010101010101",
    "0321023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb",
    "0329023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb0000000000000001",
    "0330023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb000000000000000100000000000001",
    "0331043da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb00000000000000010000000000000002",
    "0332023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb0000000000000001000000000000000001",
    "fd00fe00",
    "fd00fe0101",
    "fd00fe03010101",
    "0000",
]

# from: https://github.com/lightningnetwork/lightning-rfc/blob/4c3d01616d8e7c1c39212f97562964eceb769c08/01-messaging.md#tlv-decoding-successes
TEST_BOTH_NAMESPACES_VALID_IGNORED = [
    "",
    "2100",
    "fd020100",
    "fd00fd00",
    "fd00ff00",
    "fe0200000100",
    "ff020000000000000100",
]

# from: https://github.com/lightningnetwork/lightning-rfc/blob/4c3d01616d8e7c1c39212f97562964eceb769c08/01-messaging.md#tlv-decoding-successes
TEST_NAMESPACE1_VALID = [
    {'stream':   "0100",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 0}},
    },
    {'stream':   "010101",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 1}},
    },
    {'stream':   "01020100",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 256}},
    },
    {'stream':   "0103010000",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 65536}},
    },
    {'stream':   "010401000000",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 16777216}},
    },
    {'stream':   "0106010000000000",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 1099511627776}},
    },
    {'stream':   "010701000000000000",
     'expected': {1: {'tlv_type_name': 'tlv1', "amount_msat": 281474976710656}},
    },
    {'stream':   "01080100000000000000",
     'expected': {1: {'tlv_type_name': 'tlv1',
                      "amount_msat": 72057594037927936}},
    },
    {'stream':   "0331023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb00000000000000010000000000000002",
     'expected': {3: {'tlv_type_name': 'tlv3',
                      "node_id":        "023da092f6980e58d2c037173180e9a465476026ee50f96695963e8efe436f54eb",
                      "amount_msat_1":  1,
                      "amount_msat_2":  2}}
    },
    {'stream':   "fd00fe020226",
     'expected': {254: {'tlv_type_name': 'tlv4', "cltv_delta": 550}},
    },
]

# from: https://github.com/lightningnetwork/lightning-rfc/blob/4c3d01616d8e7c1c39212f97562964eceb769c08/01-messaging.md#tlv-stream-decoding-failure
TEST_NAMESPACE1_DECODING_FAILURE = [
    "0208000000000000022601012a",
    "0208000000000000023102080000000000000451",
    "1f000f012a",
    "1f001f012a",
]

# from: https://github.com/lightningnetwork/lightning-rfc/blob/4c3d01616d8e7c1c39212f97562964eceb769c08/01-messaging.md#tlv-stream-decoding-failure
TEST_NAMESPACE2_DECODING_FAILURE = [
    "ffffffffffffffffff000000"
]


def json_cmp(obj1, obj2):
    # slow, lame, but it works. Take the afternoon off.
    return json.dumps(obj1, sort_keys=True) == json.dumps(obj1, sort_keys=True)

if __name__ == "__main__":
    print("testing decoding failure for both namespaces")
    for test in TEST_BOTH_NAMESPACES_INVALID:
        test_bytes = h2b(test)
        n1 = TestNamespace1()
        parsed, err = n1.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is not None, "expected err"
        n2 = TestNamespace2()
        parsed, err = n2.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is not None, "expected err"
    print("done testing decoding failure for both namespaces")

    print("testing namespace 1 invalid")
    for test in TEST_NAMESPACE1_INVALID:
        test_bytes = h2b(test)
        n1 = TestNamespace1()
        parsed, err = n1.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is not None, "expected err"
    print("done testing namespace 1 invalid")

    print("testing both namespaces valid ignored")
    for test in TEST_BOTH_NAMESPACES_VALID_IGNORED:
        test_bytes = h2b(test)
        n1 = TestNamespace1()
        parsed, err = n1.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is None, "expected no err"
        parsed_type_names = set(p['tlv_type_name'] for p in parsed.values())
        assert parsed_type_names.issubset({"unknown"}), "got non-unknown tlv"
        n2 = TestNamespace2()
        parsed, err = n2.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is None, "expected no err"
        parsed_type_names = set(p['tlv_type_name'] for p in parsed.values())
        assert parsed_type_names.issubset({"unknown"}), "got non-unknown tlv"
    print("done testing both namespaces valid ignored")

    print("testing namespace1 valid")
    for test in TEST_NAMESPACE1_VALID:
        test_bytes = h2b(test['stream'])
        n1 = TestNamespace1()
        parsed, err = n1.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is None, "expected no err"
        assert json_cmp(parsed, test['expected']), "unexpected parsed result"
    print("done testing namespace1 valid")

    print("testing namespace1 decoding falure")
    for test in TEST_NAMESPACE1_DECODING_FAILURE:
        test_bytes = h2b(test)
        n1 = TestNamespace1()
        parsed, err = n1.parse(test_bytes)
        print("parsed: %s err: %s" % (parsed, err))
        assert err is not None, "expected err"
    print("done testing namespace1 decoding falure")

    print("finished all tests")
