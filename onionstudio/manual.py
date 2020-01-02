import sys
from onionstudio.pixel import Pixel

class ManualToPixels:
    def __init__(self, pixels_string):
        self.pixels_string = pixels_string

    def parse_pixels(self):
        string_tokens = self.pixels_string.split("_")
        if len(string_tokens) == 0:
            return None, "no pixels given"
        if len(string_tokens) % 3 != 0:
            return None, "could not parse %s as pixels" % pixels
        pixels = []
        for i in range(0, len(string_tokens), 3):
            pixel_tokens = string_tokens[i:i+3]
            try:
                x = int(pixel_tokens[0])
                y = int(pixel_tokens[1])
                rgb = pixel_tokens[2]
                pixels.append(Pixel(x, y, rgb))
            except:
                return None, "could not interpret %s as pixel" % pixel_tokens
        return pixels, None
