# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import uuid

INVOICE_DESCRIPTION = ("circular payment invoice to deliver Onion Studio "
                       "extension payload")
SELF_PAYMENT = 1000 # in millisatoshis

class Invoice:
    def __init__(self, rpc):
        self.rpc = rpc

    def _get_payment_secret(self, bolt11):
        decoded = self.rpc.decodepay(bolt11)
        return decoded['payment_secret']

    def create_invoice(self):
        try:
            msatoshi = SELF_PAYMENT
            label = str(uuid.uuid4())
            description = INVOICE_DESCRIPTION
            invoice = self.rpc.invoice(msatoshi, label, description)
            invoice['payment_secret'] = self._get_payment_secret(
                invoice['bolt11'])
            return invoice, None
        except:
            return None, "could not create invoice"
