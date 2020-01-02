from bolt.util import h2b
from bolt.bigsize import BigSize
from bolt.tlv import Tlv
from bolt.namespace import Namespace
from bolt.hop_payload import HopPayload, TlvHopPayload

from onionstudio.pixel import Pixel, PIXEL_BYTE_SIZE

# According to BOLT 1, extension TLVs must be greater than 2^16. Odd types
# allow the TLV to be ignored if it isn't understood.
PIXEL_TLV_TYPE = 65555

class Extension:
    def _encode_pixels(pixels):
        encoded = b''.join([p.to_bin() for p in pixels])
        return Tlv(PIXEL_TLV_TYPE, encoded).encode()


    def encode_non_final(amt_to_forward, outgoing_cltv_value, short_channel_id,
                         pixels):
        unextended = TlvHopPayload.encode_non_final(amt_to_forward,
                                                    outgoing_cltv_value,
                                                    short_channel_id)
        old_len, content, err = BigSize.pop(unextended)
        assert err is None
        pixel_content = Extension._encode_pixels(pixels)
        new_content = content + pixel_content
        return BigSize.encode(len(new_content)) + new_content


    def encode_final(amt_to_forward, outgoing_cltv_value, payment_secret,
                     total_msat, pixels):
        unextended = TlvHopPayload.encode_final(amt_to_forward,
                                                outgoing_cltv_value,
                                                pament_secret=payment_secret,
                                                totol_msat= total_msat)
        old_len, content, err = BigSize.pop(unextended)
        assert err is None
        pixel_content = Extension._encode_pixels(pixels)
        new_content = content + pixel_content
        return BigSize.encode(len(new_content)) + new_content

    ###########################################################################

    def parse_pixels(tlv):
        pixels = []
        if tlv.l % PIXEL_BYTE_SIZE != 0:
            return None, "unexpected length"
        remainder = tlv.v
        while len(remainder) > 0:
            pixel_hex, remainder, err = Namespace.pop_bytes(PIXEL_BYTE_SIZE,
                                                            remainder)
            if err:
                return None, err
            pixels.append(Pixel.from_bin(h2b(pixel_hex)))
        return {'tlv_type_name': "onion_studio_pixels",
                'pixels':         pixels}, None

    def parse(byte_string):
        extension_parsers = {PIXEL_TLV_TYPE: Extension.parse_pixels}
        parsed, err = HopPayload.parse(byte_string,
                                       extension_parsers=extension_parsers)
        if err:
            return None, err
        if parsed['format'] != "tlv":
            return None, "non-tlv payload byte string"
        if PIXEL_TLV_TYPE not in parsed['tlvs']:
            return None, "no pixel data tlv in payload"
        return parsed, None
