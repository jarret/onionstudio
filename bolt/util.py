import string

def b2h(byte_string):
    """ byte string to a hex-formatted string """
    return byte_string.hex()

HEX_DIGITS = {d for d in string.hexdigits}

def h2b(hex_string):
    """ hex-formatted string to byte string """
    assert len(hex_string) % 2 == 0, "odd number of hex digits?"
    non_hex = sum(1 for c in hex_string if c not in HEX_DIGITS)
    assert non_hex == 0, "string contains non-hex digits"
    return bytes.fromhex(hex_string)

def i2b(value, n_bytes):
    """ integer value to big endian byte array """
    assert value >= 0, "can only encode unsigned integers"
    return value.to_bytes(n_bytes, byteorder="big")

def b2i(byte_string):
    """ big endian byte array to integer value """
    return int.from_bytes(byte_string, byteorder="big", signed=False)

def h2i(hex_string):
    """ big endian hex string to hex value """
    return b2i(h2b(hex_string))

def i2h(value, n_bytes):
    """ integer to big endian hex string"""
    return b2h(i2b(value, n_bytes))
