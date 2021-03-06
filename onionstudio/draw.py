# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import time
import uuid
import pprint

from onionstudio.invoice import Invoice
from onionstudio.onion import Onion

WAIT_FOR_PAYMENT_CHECKS = 20
WAIT_FOR_PAYMENT_PERIOD = 2.0

class Draw:
    def __init__(self, rpc, dst_node, pixels):
        self.rpc = rpc
        self.dst_node = dst_node
        self.pixels = pixels
        self.total_pixels = len(self.pixels)
        self.pixels_drawn = 0

    ###########################################################################

    def _get_myid(self):
        try:
            info = self.rpc.getinfo()
            return info['id']
        except:
            return None

    def _get_cltv_final(self):
        try:
            info = self.rpc.listconfigs()
            print("cltv-final: %d" % info['cltv-final'])
            return info['cltv-final']
        except:
            return None

    def _payment_status(self, payment_hash):
        try:
            l = self.rpc.listsendpays(None, payment_hash)
            status = l['payments'][0]['status']
            return status
        except:
            return "error"

    def _send_onion(self, onion, first_hop, assoc_data, shared_secrets):
        label = str(uuid.uuid4())
        #print("send params: %s %s %s %s %s" % (onion, first_hop, assoc_data,
        #                                       label, shared_secrets))
        try:
            result = self.rpc.sendonion(onion, first_hop, assoc_data, label,
                                        shared_secrets)
            return result, None
        except:
            return None, "could not send onion"

    ###########################################################################

    def _draw_pixels(self, myid, cltv_final, pixels):
        invoice, err = Invoice(self.rpc).create_invoice()
        if err:
            return None, err
        onion_creator = Onion(self.rpc, myid, cltv_final, self.dst_node,
                              invoice, pixels)
        onion_result = onion_creator.fit_onion()
        if onion_result['status'] != "success":
            return None, onion_result['msg']
        fitted_pixels = onion_result['fitted_pixels']
        result, err = self._send_onion(onion_result['onion'],
                                       onion_result['first_hop'],
                                       onion_result['assoc_data'],
                                       onion_result['shared_secrets'])
        if err:
            return None, err
        if result['status'] not in {"pending", "complete"}:
            return None, "payment status not as expected after send"
        if result['status'] == "complete":
            return result['fitted_pixels'], None
        print("waiting for payment completion")
        checks = 0
        while True:
            status = self._payment_status(onion_result['payment_hash'])
            if status == "complete":
                break
            if status != "pending":
                return None, "payment did not complete. Status: %s" % status
            checks += 1
            if checks == WAIT_FOR_PAYMENT_CHECKS:
                return None, "payment didn't complete"
            print("(%s) sleeping waiting for payment to complete..." % status)
            time.sleep(WAIT_FOR_PAYMENT_PERIOD)
        return onion_result['fitted_pixels'], None

    def _draw_loop(self, myid, cltv_final):
        pixels = self.pixels
        while True:
            pixels_drawn, err = self._draw_pixels(myid, cltv_final, pixels)
            if err:
                return err
            if pixels_drawn:
                self.pixels_drawn += pixels_drawn
                pixels = pixels[pixels_drawn:]
            if len(pixels) == 0:
                print("all pixels drawn")
                return None

    def _get_report(self):
        return {"total_pixels": self.total_pixels,
                "pixels_drawn": self.pixels_drawn}

    ###########################################################################

    def run(self):
        myid = self._get_myid()
        if not myid:
            return self._get_report(), "could not get myid"
        print("myid: %s" % (myid))
        cltv_final = self._get_cltv_final()
        if not cltv_final:
            return self._get_report(), "could not get cltv_final"
        try:
            err = self._draw_loop(myid, cltv_final)
            if err:
                return self._get_report(), err
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return self._get_report(), None, "error while buying pixels: %s" % e
        return self._get_report(), None
