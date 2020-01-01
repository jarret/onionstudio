#!/usr/bin/env python3
import os
import sys
import random

sys.path.insert(1, os.path.realpath(os.path.pardir))

from bolt.bigsize import BigSize, h2b


# From: https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#bigsize-decoding-tests

BIGSIZE_DECODING_TESTS = [
    {
        "name": "zero",
        "value": 0,
        "bytes": "00"
    },
    {
        "name": "one byte high",
        "value": 252,
        "bytes": "fc"
    },
    {
        "name": "two byte low",
        "value": 253,
        "bytes": "fd00fd"
    },
    {
        "name": "two byte high",
        "value": 65535,
        "bytes": "fdffff"
    },
    {
        "name": "four byte low",
        "value": 65536,
        "bytes": "fe00010000"
    },
    {
        "name": "four byte high",
        "value": 4294967295,
        "bytes": "feffffffff"
    },
    {
        "name": "eight byte low",
        "value": 4294967296,
        "bytes": "ff0000000100000000"
    },
    {
        "name": "eight byte high",
        "value": 18446744073709551615,
        "bytes": "ffffffffffffffffff"
    },
    {
        "name": "two byte not canonical",
        "value": 0,
        "bytes": "fd00fc",
        "exp_error": "decoded varint is not canonical"
    },
    {
        "name": "four byte not canonical",
        "value": 0,
        "bytes": "fe0000ffff",
        "exp_error": "decoded varint is not canonical"
    },
    {
        "name": "eight byte not canonical",
        "value": 0,
        "bytes": "ff00000000ffffffff",
        "exp_error": "decoded varint is not canonical"
    },
    {
        "name": "two byte short read",
        "value": 0,
        "bytes": "fd00",
        "exp_error": "unexpected EOF"
    },
    {
        "name": "four byte short read",
        "value": 0,
        "bytes": "feffff",
        "exp_error": "unexpected EOF"
    },
    {
        "name": "eight byte short read",
        "value": 0,
        "bytes": "ffffffffff",
        "exp_error": "unexpected EOF"
    },
    {
        "name": "one byte no read",
        "value": 0,
        "bytes": "",
        "exp_error": "EOF"
    },
    {
        "name": "two byte no read",
        "value": 0,
        "bytes": "fd",
        "exp_error": "unexpected EOF"
    },
    {
        "name": "four byte no read",
        "value": 0,
        "bytes": "fe",
        "exp_error": "unexpected EOF"
    },
    {
        "name": "eight byte no read",
        "value": 0,
        "bytes": "ff",
        "exp_error": "unexpected EOF"
    }
]


if __name__ == "__main__":
    print("running test cases")
    for test in BIGSIZE_DECODING_TESTS:
        #print("test: %s" % test)
        v, remainder, err = BigSize.pop(h2b(test['bytes']))
        #print("%s %s %s %s" % (test['value'], str(v), remainder, err))
        if 'exp_error' in test.keys():
            assert err is not None, "did not get error as expected"
        else:
            assert v == test['value'], "did not get value expected"
    print("passed test cases")

    print("running small")
    TEST_ITERATIONS = 10000
    for _ in range(TEST_ITERATIONS):
        v = random.randint(0, 0xfc)
        encoded = BigSize.encode(v)
        decoded, remainder, err = BigSize.pop(encoded)
        assert err is None, "unexpected error"
        assert len(remainder) == 0, "unexpected remainder"
        assert decoded == v, "got wrong value"
    print("passed small")

    print("running medium")
    for _ in range(TEST_ITERATIONS):
        v = random.randint(0, 0x1000)
        encoded = BigSize.encode(v)
        decoded, remainder, err = BigSize.pop(encoded)
        assert err is None, "unexpected error"
        assert len(remainder) == 0, "unexpected remainder"
        assert decoded == v, "got wrong value"
    print("passed medium")

    print("running big")
    for _ in range(TEST_ITERATIONS):
        v = random.randint(0, 0x10000000)
        encoded = BigSize.encode(v)
        decoded, remainder, err = BigSize.pop(encoded)
        assert err is None, "unexpected error"
        assert len(remainder) == 0, "unexpected remainder"
        assert decoded == v, "got wrong value"
    print("passed big")

    print("running yuge")
    for _ in range(TEST_ITERATIONS):
        v = random.randint(0, 0xffffffffffffffff)
        encoded = BigSize.encode(v)
        decoded, remainder, err = BigSize.pop(encoded)
        assert err is None, "unexpected error"
        assert len(remainder) == 0, "unexpected remainder"
        assert decoded == v, "got wrong value"
    print("passed yuge")
