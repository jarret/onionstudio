#!/usr/bin/env python3
import os
import sys

sys.path.insert(1, os.path.realpath(os.path.pardir))

from bolt.util import h2b
from bolt.bigsize import BigSize
from bolt.tlv import Tlv


# from: https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#tlv-decoding-successes
TLV_VALID_TESTS = [
     {'stream': "2100",
      't':      0x21,
      'l':      0,
      'v':      "",
      'r':      ""},
     {'stream': "fd020100",
      't':      0x201,
      'l':      0,
      'v':      "",
      'r':      ""},
     {'stream': "fd00fd00",
      't':      0xfd,
      'l':      0,
      'v':      "",
      'r':      ""},
     {'stream': "fd00ff00",
      't':      0xff,
      'l':      0,
      'v':      "",
      'r':      ""},
     {'stream': "fe0200000100",
      't':      0x2000001,
      'l':      0,
      'v':      "",
      'r':      ""},
     {'stream': "ff020000000000000100",
      't':      0x200000000000001,
      'l':      0,
      'v':      "",
      'r':      ""},
]


# from: https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#tlv-decoding-failures
TLV_INVALID_TESTS = [
     {'stream': ""}, # empty byte stream is counted as invalid by this lib
     {'stream': "fd"},
     {'stream': "fd01"},
     {'stream': "fd000100"},
     {'stream': "fd0101"},
     {'stream': "0ffd26"},
     {'stream': "0ffd2602"},
     {'stream': "0ffd000100"},
     {'stream': "0ffd0201000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"},
]


if __name__ == "__main__":
    print("testing valid cases")
    for test in TLV_VALID_TESTS:
        peek_tlv, peek_err = Tlv.peek(h2b(test['stream']))
        pop_tlv, remainder, pop_err = Tlv.pop(h2b(test['stream']))


        assert peek_err is None
        assert peek_tlv.t == test['t']
        assert peek_tlv.l == test['l']
        assert peek_tlv.v == h2b(test['v'])

        assert pop_err is None
        assert pop_tlv.t == test['t']
        assert pop_tlv.l == test['l']
        assert pop_tlv.v == h2b(test['v'])
        assert remainder == h2b(test['r'])

    print("done testing valid cases")
    print("testing invalid cases")
    for test in TLV_INVALID_TESTS:
        peek_tlv, peek_err = Tlv.peek(h2b(test['stream']))
        pop_tlv, remainder, pop_err = Tlv.pop(h2b(test['stream']))
        assert peek_err != None
        assert pop_err != None
    print("done testing invalid cases")

