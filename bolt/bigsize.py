# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
from bolt.util import h2b, i2b, b2i

class BigSize:
    """
    For encoding/decoding values to/from BigSize byte strings as defined in:
    https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#appendix-a-bigsize-test-vectors
    """
    @staticmethod
    def peek_8(byte_string):
        if len(byte_string) < 1:
            return None, "underrun while peeking a uint8"
        return b2i(byte_string[0:1]), None

    @staticmethod
    def peek_16(byte_string):
        if len(byte_string) < 2:
            return None, "underrun while peeking a uint16"
        val = b2i(byte_string[0:2])
        if val < 0xfd:
            return None, "not a minimally encoded unit16"
        return val, None

    @staticmethod
    def peek_32(byte_string):
        if len(byte_string) < 4:
            return None, "underrun while peeking a uint32"
        val = b2i(byte_string[0:4])
        if val < 0x10000:
            return None, "not a minimally encoded uint32"
        return val, None

    @staticmethod
    def peek_64(byte_string):
        if len(byte_string) < 8:
            return None, "underrun while peeking a uint64"
        val = b2i(byte_string[0:8])
        if val < 0x100000000:
            return None, "not a minimally encoded uint64"
        return val, None

    @staticmethod
    def peek(byte_string):
        """ Peeks a BigSize off the front of the byte string. The second
            return value is for passing an error string if there is an error or
            None otherwise. """
        head, err = BigSize.peek_8(byte_string)
        if err:
            return None, err
        if head == 0xfd:
            val, err = BigSize.peek_16(byte_string)
            return (None, err) if err else (val, None)
        elif head == 0xfe:
            val, err = BigSize.peek_32(byte_string)
            return (None, err) if err else (val, None)
        elif head == 0xff:
            val, err = BigSize.peek_64(byte_string)
            return (None, err) if err else (val, None)
        else:
            return head, None

    ###########################################################################

    @staticmethod
    def pop_8(byte_string):
        val, err = BigSize.peek_8(byte_string)
        return (None, None, err) if err else (val, byte_string[1:], None)

    @staticmethod
    def pop_16(byte_string):
        val, err = BigSize.peek_16(byte_string)
        return (None, None, err) if err else (val, byte_string[2:], None)

    @staticmethod
    def pop_32(byte_string):
        val, err = BigSize.peek_32(byte_string)
        return (None, None, err) if err else (val, byte_string[4:], None)

    @staticmethod
    def pop_64(byte_string):
        val, err = BigSize.peek_64(byte_string)
        return (None, None, err) if err else (val, byte_string[8:], None)

    @staticmethod
    def pop(byte_string):
        """ Pops a BigSize off the front of the byte string. Returns the
            decoded value and the remaining byte string. The third return
            value is for passing an error string if there is an error or None
            otherwise. """
        head, byte_string, err = BigSize.pop_8(byte_string)
        if err:
            return None, None, err
        if head == 0xfd:
            val, byte_string, err = BigSize.pop_16(byte_string)
            return (None, None, err) if err else (val, byte_string, None)
        elif head == 0xfe:
            val, byte_string, err = BigSize.pop_32(byte_string)
            return (None, None, err) if err else (val, byte_string, None)
        elif head == 0xff:
            val, byte_string, err = BigSize.pop_64(byte_string)
            return (None, None, err) if err else (val, byte_string, None)
        else:
            return head, byte_string, None

    ###########################################################################

    @staticmethod
    def encode(val):
        assert val <= 0xffffffffffffffff, "cannot encode bigger than uint64"
        if val < 0xfd:
            return i2b(val, 1)
        if val < 0x10000:
            return i2b(0xfd, 1) + i2b(val, 2)
        if val < 0x100000000:
            return i2b(0xfe, 1) + i2b(val, 4)
        else:
            return i2b(0xff, 1) + i2b(val, 8)

