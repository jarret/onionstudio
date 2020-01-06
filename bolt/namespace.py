# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
from bolt.util import b2i, b2h, h2i, h2b, i2h, i2b
from bolt.tlv import Tlv

class Namespace:
    """
    Represents a specific namespace of TLVs as referred to in BOLT 1 and
    provides generic pop helpers for the fundamental types defined here:
    https://github.com/lightningnetwork/lightning-rfc/blob/master/01-messaging.md#fundamental-types
    """
    @staticmethod
    def pop_tlv(byte_string):
        return Tlv.pop(byte_string)

    @staticmethod
    def tlvs_are_valid(byte_string):
        while len(byte_string) > 0:
            _, byte_string, err = Namespace.pop_tlv(byte_string)
            if err:
                return False
        return True

    @staticmethod
    def iter_tlvs(byte_string):
        assert Namespace.tlvs_are_valid(byte_string), "bad byte_string?"
        while len(byte_string) > 0:
            tlv, byte_string, _ = Tlv.pop(byte_string)
            yield tlv

    ###########################################################################

    @staticmethod
    def encode_bytes(hex_string):
        return h2b(hex_string)

    @staticmethod
    def pop_bytes(n_bytes, byte_string):
        if len(byte_string) < n_bytes:
            return None, None, "underrun while popping bytes"
        return b2h(byte_string[:n_bytes]), byte_string[n_bytes:], None

    ###########################################################################

    @staticmethod
    def pop_u8(byte_string):
        if len(byte_string) < 1:
            return None, None, "underrun while popping a u8"
        return b2i(byte_string[:1]), byte_string[1:], None

    @staticmethod
    def pop_u16(byte_string):
        if len(byte_string) < 2:
            return None, None, "underrun while popping a u16"
        return b2i(byte_string[:2]), byte_string[2:], None

    @staticmethod
    def pop_u32(byte_string):
        if len(byte_string) < 4:
            return None, None, "underrun while popping a u32"
        return b2i(byte_string[:4]), byte_string[4:], None

    @staticmethod
    def pop_u64(byte_string):
        if len(byte_string) < 8:
            return None, None, "underrun while popping a u64"
        return b2i(byte_string[:8]), byte_string[8:], None

    ###########################################################################

    @staticmethod
    def encode_u8(value):
        return i2b(value, 1)

    @staticmethod
    def encode_u16(value):
        return i2b(value, 2)

    @staticmethod
    def encode_u32(value):
        return i2b(value, 4)

    @staticmethod
    def encode_u64(value):
        return i2b(value, 8)

    ###########################################################################

    def minimal_tu_bytes(int_value):
        assert int_value <= 0xffffffffffffffff, "value too big for encoding"
        if int_value == 0:
            return 0
        if int_value <= 0xff:
            return 1
        if int_value <= 0xffff:
            return 2
        if int_value <= 0xffffff:
            return 3
        if int_value <= 0xffffffff:
            return 4
        if int_value <= 0xffffffffff:
            return 5
        if int_value <= 0xffffffffffff:
            return 6
        if int_value <= 0xffffffffffffff:
            return 7
        if int_value <= 0xffffffffffffffff:
            return 8

    @staticmethod
    def pop_tu16(n_bytes, byte_string):
        if n_bytes > 2:
            return None, None, "cannot pop more than 2 bytes for a tu16"
        if len(byte_string) < n_bytes:
            return None, None, "underrun while popping tu16"
        if n_bytes == 0:
            return 0, byte_string, None
        val = b2i(byte_string[:n_bytes])
        if n_bytes != Namespace.minimal_tu_bytes(val):
            return None, None, "not minimal encoding for value"
        return val, byte_string[n_bytes:], None

    @staticmethod
    def pop_tu32(n_bytes, byte_string):
        if n_bytes > 4:
            return None, None, "cannot pop more than 4 bytes for a tu32"
        if len(byte_string) < n_bytes:
            return None, None, "underrun while popping tu32"
        if n_bytes == 0:
            return 0, byte_string, None
        val = b2i(byte_string[:n_bytes])
        if n_bytes != Namespace.minimal_tu_bytes(val):
            return None, None, "not minimal encoding for value"
        return val, byte_string[n_bytes:], None

    @staticmethod
    def pop_tu64(n_bytes, byte_string):
        if n_bytes > 8:
            return None, None, "cannot pop more than 8 bytes for a tu64"
        if len(byte_string) < n_bytes:
            return None, None, "underrun while popping tu62"
        if n_bytes == 0:
            return 0, byte_string, None
        val = b2i(byte_string[:n_bytes])
        if n_bytes != Namespace.minimal_tu_bytes(val):
            return None, None, "not minimal encoding for value"
        return val, byte_string[n_bytes:], None

    ###########################################################################

    @staticmethod
    def encode_tu(value):
        n_bytes = Namespace.minimal_tu_bytes(value)
        if n_bytes == 0:
            return b''
        return i2b(value, n_bytes)

    @staticmethod
    def encode_tu16(value):
        assert value <= 0xffff, "value too big for tu16"
        return Namespace.encode_tu(value)

    @staticmethod
    def encode_tu32(value):
        assert value <= 0xffffffff, "value too big for tu32"
        return Namespace.encode_tu(value)

    @staticmethod
    def encode_tu64(value):
        assert value <= 0xffffffffffffffff, "value too big for tu64"
        return Namespace.encode_tu(value)

    ###########################################################################

    @staticmethod
    def pop_chain_hash(byte_string):
        if not len(byte_string) >= 32:
            return None, None, "underrun while popping chain_hash"
        return b2h(byte_string)[:32], byte_string[32:], None

    @staticmethod
    def pop_channel_id(byte_string):
        if not len(byte_string) >= 32:
            return None, None, "underrun while popping channel_id"
        return b2h(byte_string[:32]), byte_string[32:], None

    @staticmethod
    def pop_sha256(byte_string):
        if not len(byte_string) >= 64:
            return None, None, "underrun while popping signature"
        return b2h(byte_string[:64]), byte_string[64:], None

    @staticmethod
    def pop_signature(byte_string):
        if not len(byte_string) >= 64:
            return None, None, "underrun while popping signature"
        return b2h(byte_string[:64]), byte_string[64:], None

    @staticmethod
    def pop_point(byte_string):
        if not len(byte_string) >= 33:
            return None, None, "underrun wihle popping point"
        point = b2h(byte_string[:33])
        if not point.startswith("02") and not point.startswith("03"):
            return None, None, "not valid compressed point"
        return point, byte_string[33:], None

    @staticmethod
    def pop_short_channel_id(byte_string):
        if not len(byte_string) >= 8:
            return None, None, "underrun while popping short_channel_id"
        block_height = b2i(byte_string[:3])
        tx_index = b2i(byte_string[3:6])
        output_index = b2i(byte_string[6:8])
        formatted = "%dx%dx%d" % (block_height, tx_index, output_index)
        return formatted, byte_string[8:], None

    ###########################################################################

    @staticmethod
    def encode_short_channel_id(short_channel_id):
        values = short_channel_id.split("x")
        assert len(values) == 3, "not a short_channel_id string"
        try:
            block_height = int(values[0])
            tx_index = int(values[1])
            output_index = int(values[2])
        except:
            assert False, "not a short_channel_id string"
        return i2b(block_height, 3) + i2b(tx_index, 3) + i2b(output_index, 2)

    ###########################################################################

    @staticmethod
    def encode_tlv(t, v):
        return Tlv(t, v).encode()

    ###########################################################################

    @staticmethod
    def parse_tlv(tlv, tlv_parsers):
        if tlv.t not in tlv_parsers:
            return {"tlv_type_name": "unknown",
                    "type":          tlv.t,
                    "value":         b2h(tlv.v)}, None
            return False, "TLV type has no defined parser function"
        parsed_tlv, err = tlv_parsers[tlv.t](tlv)
        if err:
            return False, err
        assert 'tlv_type_name' in parsed_tlv, ("subclass parser must name the "
                                               "parsed tlv type")
        return parsed_tlv, None

    @staticmethod
    def parse_tlvs(tlvs, tlv_parsers):
        parsed_tlvs = {}
        for tlv in tlvs:
            parsed_tlv, err = Namespace.parse_tlv(tlv, tlv_parsers)
            if err:
                return None, err
            parsed_tlvs[tlv.t] = parsed_tlv
        return parsed_tlvs, None

    @staticmethod
    def _has_unknown_even_types(tlvs, tlv_parsers):
        present = set(tlv.t for tlv in tlvs)
        known = set(tlv_parsers.keys())
        unknown = present.difference(known)
        for t in list(unknown):
            if t % 2 == 0:
                return True
        return False

    @staticmethod
    def _ordered_ascending(tlvs):
        if len(tlvs) == 0:
            return True
        if len(tlvs) == 1:
            return True
        max_type = tlvs[0].t
        for tlv in tlvs[1:]:
            if tlv.t <= max_type:
                return False
            max_type = tlv.t
        return True

    @staticmethod
    def _has_duplicates(tlvs):
        types = [tlv.t for tlv in tlvs]
        dedupe = set(tlv.t for tlv in tlvs)
        return len(types) != len(dedupe)

    @staticmethod
    def parse(byte_string, tlv_parsers):
        if not Namespace.tlvs_are_valid(byte_string):
            return None, "tlvs are not valid"
        tlvs = list(Namespace.iter_tlvs(byte_string))
        if Namespace._has_unknown_even_types(tlvs, tlv_parsers):
            return None, "got unknown even type tlv for Namespace"
        if Namespace._has_duplicates(tlvs):
            return None, "duplicate TLVs in stream"
        if not Namespace._ordered_ascending(tlvs):
            return None, "tlvs values not ascending"
        parsed_tlvs, err = Namespace.parse_tlvs(tlvs, tlv_parsers)
        if err:
            return None, err
        return parsed_tlvs, None

