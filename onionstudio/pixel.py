import string

MAX_X = 1024
MAX_Y = 1024

PIXEL_BYTE_SIZE = 4

# |---10 bit x---|---10 bit y---|---12 bit rgb---|

class Pixel(object):
    def __init__(self, x, y, rgb):
        assert x < MAX_X
        assert x >= 0
        assert y < MAX_Y
        assert y >= 0
        for c in rgb:
            assert c in string.hexdigits
        print(rgb)
        if len(rgb) == 6:
            rgb = Pixel.clamp_rgb(rgb)
        print(rgb)
        assert len(rgb) == 3

        self.x = x
        self.y = y
        self.rgb = rgb

    def __str__(self):
        return "(%d,%d,%s)" % (self.x, self.y, self.rgb)

    def clamp_rgb(rgb_24):
        assert len(rgb_24) == 6
        return rgb_24[0] + rgb_24[2] + rgb_24[4]

    def from_bin(pixel_bin):
        print("bin: %s" % pixel_bin.hex())
        assert len(pixel_bin) == PIXEL_BYTE_SIZE
        val = int.from_bytes(pixel_bin, byteorder="big")
        x = val >> 22 & 0x03ff
        y = val >> 12 & 0x03ff
        rgb = ("%03x" % (val & 0x0fff))[0:3]
        return Pixel(x, y, rgb)

    def to_bin(self):
        x_shifted = self.x << 22
        y_shifted = self.y << 12
        rgb_int =  int("0" + self.rgb, 16)
        val = x_shifted | y_shifted | rgb_int
        rgb_bin = bytearray.fromhex("0" + self.rgb)
        return val.to_bytes(4, byteorder="big")
