# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
from bolt.bigsize import BigSize
from bolt.tlv import Tlv
from bolt.namespace import Namespace

###############################################################################

class LegacyHopPayload:
    """ encodes/parses legacy hop payloads as described in:
    https://github.com/lightningnetwork/lightning-rfc/blob/master/04-onion-routing.md
    """

    @staticmethod
    def encode(short_channel_id, amt_to_forward, outgoing_cltv_value):
        encoded_version = Namespace.encode_u8(0)
        encoded_scid = Namespace.encode_short_channel_id(short_channel_id)
        encoded_amt = Namespace.encode_u64(amt_to_forward)
        encoded_outgoing = Namespace.encode_u32(outgoing_cltv_value)
        padding = 12 * Namespace.encode_u8(0)
        return (encoded_version + encoded_scid + encoded_amt +
                encoded_outgoing + padding)

    @staticmethod
    def parse(byte_string):
        scid, remainder, err = Namespace.pop_short_channel_id(byte_string)
        if err:
            return None, err
        #print("scid: %s, remainder: %s\n" % (scid, remainder.hex()))
        amt_to_forward, remainder, err = Namespace.pop_u64(remainder)
        if err:
            return None, err
        #print("amt: %s, remainder: %s\n" % (amt_to_forward, remainder.hex()))
        outgoing_cltv_value, remainder, err = Namespace.pop_u32(remainder)
        if err:
            return None, err
        #print("outgoing: %s,  remainder: %s\n" % (outgoing_cltv_value,
        #                                          remainder.hex()))
        padding, remainder, err = Namespace.pop_bytes(12, remainder)
        if err:
            return None, err
        #print("padding %s, remainder: %s\n" % (padding, remainder.hex()))
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'format':              'legacy',
                'short_channel_id':    scid,
                'amt_to_forward':      amt_to_forward,
                'outgoing_cltv_value': outgoing_cltv_value,
                'padding':             padding}, None


###############################################################################

class TlvHopPayload:
    """ encodes/parsers tlv payloads as described in:
    https://github.com/lightningnetwork/lightning-rfc/blob/master/04-onion-routing.md
    """

    @staticmethod
    def parse_amt_to_forward(tlv):
        amt_to_forward, remainder, err = Namespace.pop_tu64(tlv.l, tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name': 'amt_to_forward',
                'amt_to_forward': amt_to_forward}, None

    @staticmethod
    def parse_outgoing_cltv_value(tlv):
        outgoing_cltv_value, remainder, err = Namespace.pop_tu32(tlv.l, tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name':      'outgoing_cltv_value',
                'outgoing_cltv_value': outgoing_cltv_value}, None

    @staticmethod
    def parse_short_channel_id(tlv):
        scid, remainder, err = Namespace.pop_short_channel_id(tlv.v)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name':   'short_channel_id',
                'short_channel_id': scid}, None

    @staticmethod
    def parse_payment_data(tlv):
        payment_secret, remainder, err = Namespace.pop_bytes(32, tlv.v)
        if err:
            return None, err
        total_msat, remainder, err = Namespace.pop_tu64(len(remainder),
                                                        remainder)
        if err:
            return None, err
        if len(remainder) != 0:
            return None, "unexpected remaining bytes"
        return {'tlv_type_name':  'payment_data',
                'payment_secret': payment_secret,
                'total_msat':     total_msat}, None

    ###########################################################################

    @staticmethod
    def encode_amt_to_forward(amt_to_forward):
        return Tlv(2, Namespace.encode_tu64(amt_to_forward)).encode()

    @staticmethod
    def encode_outgoing_cltv_value(outgoing_cltv_value):
        return Tlv(4, Namespace.encode_tu32(outgoing_cltv_value)).encode()

    @staticmethod
    def encode_short_channel_id(short_channel_id):
        t = Tlv(6, Namespace.encode_short_channel_id(short_channel_id))
        return t.encode()

    @staticmethod
    def encode_payment_data(payment_secret, total_msat):
        body = (Namespace.encode_bytes(payment_secret) +
                Namespace.encode_tu64(total_msat))
        return Tlv(8, body).encode()

    ###########################################################################

    @staticmethod
    def encode_non_final(amt_to_forward, outgoing_cltv_value, short_channel_id):
        payload = (
            TlvHopPayload.encode_amt_to_forward(amt_to_forward) +
            TlvHopPayload.encode_outgoing_cltv_value(outgoing_cltv_value) +
            TlvHopPayload.encode_short_channel_id(short_channel_id))
        return BigSize.encode(len(payload)) + payload


    @staticmethod
    def encode_final(amt_to_forward, outgoing_cltv_value, payment_secret=None,
                     total_msat=None):
        payload = (
            TlvHopPayload.encode_amt_to_forward(amt_to_forward) +
            TlvHopPayload.encode_outgoing_cltv_value(outgoing_cltv_value))
        if payment_secret:
            assert total_msat != None, "payment_secret without total_msat"
            payload += TlvHopPayload.encode_payment_data(payment_secret,
                                                         total_msat)
        return BigSize.encode(len(payload)) + payload

    @staticmethod
    def encode_custom_test(amt_to_forward=None, outgoing_cltv_value=None,
                           short_channel_id=None, payment_data=None):
        # prepares a payload that may violate some of the BOLT 4 tlv payload
        # rules
        payload = b''
        if amt_to_forward:
            payload += TlvHopPayload.encode_amt_to_forward(amt_to_forward)
        if outgoing_cltv_value:
            payload += (
                TlvHopPayload.encode_outgoing_cltv_value(outgoing_cltv_value))
        if short_channel_id:
            payload += TlvHopPayload.encode_short_channel_id(short_channel_id)
        if payment_data:
            payload += (
                TlvHopPayload.encode_payment_data(payment_data[0],
                                                  payment_data[1]))
        return BigSize.encode(len(payload)) + payload

    ###########################################################################

    @staticmethod
    def parse(byte_string, extension_parsers=None):
        tlv_parsers = {2: TlvHopPayload.parse_amt_to_forward,
                       4: TlvHopPayload.parse_outgoing_cltv_value,
                       6: TlvHopPayload.parse_short_channel_id,
                       8: TlvHopPayload.parse_payment_data}
        if extension_parsers:
            tlv_parsers.update(extension_parsers)
        parsed, err = Namespace.parse(byte_string, tlv_parsers)
        if err:
            print("err 123: %s" % err)
            return None, err
        return {'format': 'tlv',
                'tlvs':   parsed}, None

    @staticmethod
    def check_non_final(parsed):
        if 2 not in parsed['tlvs']:
            return "does not include amt_to_forward"
        if 4 not in parsed['tlvs']:
            return "does not include outgoing_cltv_value"
        if 6 not in parsed['tlvs']:
            return "does not include short_channel_id in non-final hop"
        if 8 in parsed['tlvs']:
            return "payment_data included in non-final hop"
        return None

    @staticmethod
    def check_final(parsed):
        if 2 not in parsed['tlvs']:
            return "does not include amt_to_forward"
        if 4 not in parsed['tlvs']:
            return "does not include outgoing_cltv_value"
        if 6 in parsed['tlvs']:
            return "includes short_channel_id in final hop"
        return None


###############################################################################

class HopPayload:
    @staticmethod
    def parse(byte_string, extension_parsers=None):
        length, remainder, err = BigSize.pop(byte_string)
        if err:
            return None, err
        if length == 1:
            return None, "unknown version"
        if length == 0:
            return LegacyHopPayload.parse(remainder)
        if len(remainder) != length:
            return None, "remainder length does not match state length"
        return TlvHopPayload.parse(remainder,
                                   extension_parsers=extension_parsers)

    @staticmethod
    def check_non_final(parsed):
        return TlvHopPayload.check_non_final(parsed)

    @staticmethod
    def check_final(parsed):
        return TlvHopPayload.check_final(parsed)
