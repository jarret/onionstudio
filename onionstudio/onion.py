import math
import pprint

from pyln.client import Millisatoshi

from onionstudio.pixel import PIXEL_BYTE_SIZE
from onionstudio.extension import Extension
from onionstudio.invoice import SELF_PAYMENT

from bolt.util import h2b
from bolt.hop_payload import LegacyHopPayload, TlvHopPayload


RISK_FACTOR = 10
CLTV_FINAL = 10
ONION_SIZE = 1300
INITIAL_HOP_GUESS = 4

FIT_ONION_TRIES = 5

class Onion:
    def __init__(self, rpc, myid, dst_node, block_height, invoice, art_no,
                 available_pixels):
        """
        Finds a valid onion to route to the destination node that fits as many
        pixels as possible with appropriate payment
        """
        self.rpc = rpc
        self.myid = myid
        self.dst_node = dst_node
        self.block_height = block_height
        self.invoice = invoice
        self.payment_secret = self.invoice['payment_secret']
        self.payment_hash = self.invoice['payment_hash']
        self.art_no = art_no
        self.available_pixels = available_pixels

    def print_dict(self, info):
        pprint.pprint(info)

    ###########################################################################

    def _estimate_routing_bytes(self, n_hops):
        # WARNING - this is a fudge, variable sizes can't easily be anticpated
        # hard to estmiate due to variable encoding
        #
        # Perhaps more exact knowledge of the onion packet's construction in
        # BOLT 4 could be better encoded here.
        #
        # legacy payloads == 33 bytes + 32 byte hmac
        # tlv mid payloads ~= 18 bytes + 32 byte hmac
        # tlv final payloads ~= 46 bytes + 32 byte hmac
        if n_hops == 1:
            # destination is only hop
            return 46 + 32
        # assume along circular route, target mid hops and self is tlv
        # the rest are legacy
        est = 0
        # end tlv hop
        est += 46 + 32
        # target mid hop
        est += 18 + 32
        # other hops
        est += (33 + 32) * (n_hops - 2)
        return est + 10 # since this is a fudge overestimate a bit

    def _estimate_payload_pixels(self, n_hops):
        approx_bytes = ONION_SIZE - self._estimate_routing_bytes(n_hops)
        approx_pixels = math.floor(approx_bytes / PIXEL_BYTE_SIZE)
        return approx_pixels - 3 # underestimate a bit

    ###########################################################################

    def _get_outgoing_route(self, dst_payment):
        try:
            r = self.rpc.getroute(self.dst_node, SELF_PAYMENT + dst_payment,
                                  RISK_FACTOR)
            return r, None
        except:
            return None, "could not find route to %s" % (self.dst_node)

    def _get_returning_route(self, myid):
        try:
            r = self.rpc.getroute(myid, SELF_PAYMENT, RISK_FACTOR,
                                  fromid=self.dst_node)
            return r, None
        except:
            return None, "could not find route from %s to %s" % (self.dst_node,
                                                                 myid)

    def _rework_routing_fees(self, route, pay_dst, pay_msat):
        # Thanks to sendinvoiceless.py plugin for this logic!
        delay = int(CLTV_FINAL)
        msatoshi = Millisatoshi(SELF_PAYMENT)
        for r in reversed(route):
            r['msatoshi'] = msatoshi.millisatoshis
            r['amount_msat'] = msatoshi
            r['delay'] = delay
            channels = self.rpc.listchannels(r['channel'])
            ch = next(c for c in channels.get('channels') if
                      c['destination'] == r['id'])
            fee = Millisatoshi(ch['base_fee_millisatoshi'])
            # BOLT #7 requires fee >= fee_base_msat + ( amount_to_forward *
            # fee_proportional_millionths / 1000000 )
            fee += (msatoshi * ch['fee_per_millionth'] + 10**6 - 1) // 10**6
            # integer math trick to round up
            if ch['source'] == pay_dst:
                fee += pay_msat
            msatoshi += fee
            delay += ch['delay']
            r['direction'] = int(ch['channel_flags']) % 2

    def _assemble_circular(self, outgoing, returning, dst_payment):
        circular = outgoing['route'] + returning['route']
        self._rework_routing_fees(circular, self.dst_node, dst_payment)
        return circular

    def _get_circular(self, hop_count, pixel_underestimate, dst_payment):
        outgoing, err = self._get_outgoing_route(dst_payment)
        if err:
            return {'status': "err", 'msg': err}
        print("found outgoing route to destination:")
        self.print_dict(outgoing)
        returning, err = self._get_returning_route(self.myid)
        if err:
            return {'status': "err", 'msg': err}
        print("found returning route back to ourselves:")
        self.print_dict(returning)
        needed_hops = len(outgoing) + len(returning)
        if needed_hops != hop_count:
            print("different hop count than expected, need to recalculate...")
            return {'status':              "recalculate",
                    "needed_hops":         needed_hops,
                    "pixel_underestimate": pixel_underestimate}
        circular = self._assemble_circular(outgoing, returning, dst_payment)
        print("assembled circular route:")
        self.print_dict(circular)
        return {'status':   "success",
                "circular": circular}

    ###########################################################################

    def _encode_non_final(self, pubkey, channel, msatoshi, block_height,
                          delay, pixels):
        if pubkey == self.dst_node:
            p = Extension.encode_non_final(msatoshi, block_height + delay,
                                           channel, self.art_no, pixels)
        else:
            p = TlvHopPayload.encode_non_final(msatoshi, block_height + delay,
                                               channel)
        return {'style':   "tlv",
                'pubkey':  pubkey,
                'payload': p.hex()}

    def _encode_final(self, pubkey, channel, msatoshi, block_height, delay,
                      payment_secret, pixels):
        if pubkey == self.dst_node:
            p = Extension.encode_final(msatoshi, block_height + delay, channel,
                                       payment_secret, msatoshi, self.art_no,
                                       pixels)
        else:
            p = TlvHopPayload.encode_final(msatoshi, block_height + delay,
                                           payment_secret=payment_secret,
                                           total_msat=msatoshi)
        return {'style':   "tlv",
                'pubkey':  pubkey,
                'payload': p.hex()}

    def _encode_legacy(self, pubkey, channel, msatoshi, block_height, delay):
        p = LegacyHopPayload.encode(channel, msatoshi, block_height + delay)
        return {'style':   "legacy",
                'pubkey':  pubkey,
                'payload': p.hex()}

    def _iter_hops(self, circular, block_height, payment_secret, pixels):
        for i in range(len(circular) - 1):
            src = circular[i]
            dst = circular[i + 1]
            if src['style'] == 'legacy':
                yield self._encode_legacy(src['id'], dst['channel'],
                                          dst['msatoshi'], block_height,
                                          dst['delay'])
            else:
                yield self._encode_non_final(src['id'], dst['channel'],
                                             dst['msatoshi'], block_height,
                                             dst['delay'], pixels)
        dst = circular[-1]
        if dst['style'] == 'legacy':
            yield self._encode_legacy(dst['id'], dst['channel'],
                                      dst['msatoshi'], block_height,
                                      dst['delay'])
        else:
            yield self._encode_final(dst['id'], dst['channel'],
                                     dst['msatoshi'], block_height,
                                     dst['delay'], payment_secret, pixels)

    def _assemble_hops(self, circular, block_height, payment_secret, pixels):
        return list(self._iter_hops(circular, block_height, payment_secret,
                                    pixels))

    def _sum_payload_sizes(self, hops):
        total = 0
        for hop in hops:
            payload_len = len(h2b(hop['payload']))
            hmac_len = 32 # include hmac byytes needed when packed in onion
            total += payload_len + hmac_len
        return total

    def _get_hops(self, hop_count, pixel_underestimate, dst_payment,
                  attempting_pixel_list):
        result = self._get_circular(hop_count, pixel_underestimate, dst_payment)
        if result['status'] in {'recalculate', 'err'}:
            return result
        circular = result['circular']

        hops = self._assemble_hops(circular, self.block_height,
                                   self.payment_secret, attempting_pixel_list)
        print("generated hops:")
        self.print_dict(hops)
        if self._sum_payload_sizes(hops) > ONION_SIZE:
            print("payloads are too big, retrying with less pixels")
            return {'status':              "recalculate",
                    "needed_hops":         needed_hops,
                    "pixel_underestimate": pixel_underestimate + 3}
        return {'status':    'success',
                'hops':      hops,
                'first_hop': circular[0]}


    ###########################################################################

    def _slice_pixels(self, hop_count, pixel_underestimate):
        will_fit = self._estimate_payload_pixels(hop_count)
        print("it's estimated that %d pixels will fit" % will_fit)
        attempting_pixels = (min(will_fit, len(self.available_pixels)) -
                             pixel_underestimate)
        print("attempting to fit %d pixels" % attempting_pixels)
        dst_payment = 1000 * attempting_pixels
        print("attempting onion that pays the destination %dmsat" % dst_payment)
        pixels = self.available_pixels[:attempting_pixels]
        return dst_payment, pixels

    def _create_onion(self, hops, assocdata):
        try:
            result = self.rpc.createonion(hops, assocdata)
            return result['onion'], result['shared_secrets'], None
        except:
            return None, None, "could not create onion"

    def _fit_attempt(self, hop_count, pixel_underestimate):
        dst_payment, pixels = self._slice_pixels(hop_count,
                                                            pixel_underestimate)
        result = self._get_hops(hop_count, pixel_underestimate, dst_payment,
                                pixels)
        if result['status'] in {'recalculate', 'err'}:
            return result
        hops = result['hops']
        first_hop = result['first_hop']
        onion, shared_secrets, err = self._create_onion(hops, self.payment_hash)
        if err:
            return {'status': "err",
                    'msg':    err}
        print("onion: %s" % onion)
        print("shared_secrets: %s" % str(shared_secrets))
        return {'status':         "success",
                'onion':          onion,
                'first_hop':      first_hop,
                'assoc_data':     self.invoice['payment_hash'],
                'payment_hash':   self.invoice['payment_hash'],
                'shared_secrets': shared_secrets,
                'fitted_pixels':  len(pixels)}

    ###########################################################################

    def fit_onion(self):
        hop_count = INITIAL_HOP_GUESS
        pixel_underestimate = 0
        retry_count = 0
        while retry_count < FIT_ONION_TRIES:
            result = self._fit_attempt(hop_count, pixel_underestimate)
            if result['status'] == "success":
                return result
            elif result['status'] == "recalculate":
                retry_count += 1
                hop_count = result['needed_hops']
                pixel_underestimate = result['pixel_underestimate']
            elif result['status'] == 'err':
                return result
        return {'status': "err",
                'msg': "could not fit onion after %d tries" % FIT_ONION_TRIES}
