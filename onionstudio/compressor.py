# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import zlib

def compressor(bin_to_compress):
        wbits = zlib.MAX_WBITS | 16
        compress_obj = zlib.compressobj(wbits=wbits)
        a = compress_obj.compress(bin_to_compress)
        b = compress_obj.flush()
        return a + b
