import zlib

def compressor(bin_to_compress):
        wbits = zlib.MAX_WBITS | 16
        compress_obj = zlib.compressobj(wbits=wbits)
        a = compress_obj.compress(bin_to_compress)
        b = compress_obj.flush()
        return a + b
