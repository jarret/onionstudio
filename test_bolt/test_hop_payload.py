#!/usr/bin/env python3
import os
import sys
import random
import json

sys.path.insert(1, os.path.realpath(os.path.pardir))

from bolt.util import h2b
from bolt.hop_payload import HopPayload, TlvHopPayload

TEST_LEGACY_PAYLOADS = [
    {'stream': "00000067000001000100000000000003e90000007b000000000000000000000000",
     'result': {'format': 'legacy', 'short_channel_id': '103x3x1',
                'amt_to_forward': 1000, 'outgoing_cltv_value': 117,
                'padding': '000000000000000000000000'}
    },
    {'stream': "00000067000003000100000000000003e800000075000000000000000000000000",
     'result': {'format': 'legacy', 'short_channel_id': '103x3x1',
                'amt_to_forward': 1000, 'outgoing_cltv_value': 117,
                'padding': '000000000000000000000000'}
    },
]

TEST_TLV_PAYLOADS = [
    {'stream': "11020203e8040137060800007b0001c80044",
     'result':  {'format': 'tlv',
                 'tlvs': {2: {'tlv_type_name':       'amt_to_forward',
                              'amt_to_forward':      1000},
                          4: {'tlv_type_name':       'outgoing_cltv_value',
                              'outgoing_cltv_value': 55},
                          6: {'tlv_type_name':       'short_channel_id',
                              'short_channel_id':    '123x456x68'}}},
     'check': TlvHopPayload.check_non_final},
    {'stream': "07020203e8040137",
     'result': {'format': 'tlv',
                'tlvs': {2: {'tlv_type_name':        'amt_to_forward',
                             'amt_to_forward':        1000},
                         4: {'tlv_type_name':         'outgoing_cltv_value',
                             'outgoing_cltv_value':   55}}},
     'check': TlvHopPayload.check_final},
    {'stream': "2b020203e8040137082284746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d03e8",
     'result': {'format': 'tlv',
                'tlvs': {2: {'tlv_type_name': 'amt_to_forward',
                             'amt_to_forward': 1000},
                         4: {'tlv_type_name': 'outgoing_cltv_value',
                             'outgoing_cltv_value': 55},
                         8: {'tlv_type_name':  'payment_data',
                             'payment_secret': '84746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d',
                             'total_msat':      1000}}},
     'check': TlvHopPayload.check_final},
]

TEST_BAD_NON_FINAL_PAYLOADS = [
    "04020203e8",
    "0304011e",
    "07020203e804011e",
    "35020203e804011e06080000010000020003082284746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d03e8",
]

TEST_BAD_FINAL_PAYLOADS = [
    "35020207d004010a06080000040000020001082284746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d0fa0",
    "3104010a06080000040000020001082284746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d0fa0",
    "28020203e8082284746e56bfaa5ade0720b28f8dd6ac3be77ffe541d1f6bc3be35b32292e0443d03e8",
]



def json_cmp(obj1, obj2):
    # slow, lame, but it works. Take the afternoon off.
    return json.dumps(obj1, sort_keys=True) == json.dumps(obj1, sort_keys=True)


if __name__ == "__main__":
    print("testing legacy payloads")
    for test in TEST_LEGACY_PAYLOADS:
        parsed, err = HopPayload.parse(h2b(test['stream']))
        print(parsed)
        print(err)
        assert err is None, "unexpected error"
        assert json_cmp(parsed, test['result']), "unexpected result"
    print("done testing legacy payloads")


    print("testing tlv payloads")
    for test in TEST_TLV_PAYLOADS:
        parsed, err = HopPayload.parse(h2b(test['stream']))
        print(parsed)
        assert err is None, "unexpected error"
        assert json_cmp(parsed, test['result']), "unexpected result"
        check_err = test['check'](parsed)
        print(check_err)
        assert check_err is None, "did not pass check"
    print("done testing tlv payloads")

    print("testing bad non-final hop payloads")
    for test in TEST_BAD_NON_FINAL_PAYLOADS:
        parsed, err = HopPayload.parse(h2b(test))
        print(err)
        assert err is None, "unexpected error"
        check_err = TlvHopPayload.check_non_final(parsed)
        print(check_err)
        assert check_err is not None, "unexpected success"
    print("done testing bad non-final hop payloads")

    print("testing bad final hop payloads")
    for test in TEST_BAD_FINAL_PAYLOADS:
        parsed, err = HopPayload.parse(h2b(test))
        print(err)
        assert err is None, "unexpected error"
        check_err = TlvHopPayload.check_final(parsed)
        print(check_err)
        assert check_err is not None, "unexpected success"
    print("done testing bad final hop payloads")
