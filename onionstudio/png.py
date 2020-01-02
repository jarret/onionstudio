from onionstudio.pixel import Pixel

class PngToPixels:
    def __init__(self, png_file):
        from PIL import Image
        self.img = Image.open(png_file)

    def iter_at_offset(self, x_offset, y_offset):
        width, height = self.img.size
        rgb_raw = self.img.convert("RGBA")
        px_data = list(rgb_raw.getdata())
        pixels = []
        for h in range(height):
            for w in range(width):
                x = w + x_offset
                if x >= 1024:
                    continue
                y = h + y_offset
                if y >= 1024:
                    continue
                y = h + y_offset
                idx = (h * width) + w
                r = px_data[idx][0]
                g = px_data[idx][1]
                b = px_data[idx][2]
                a = px_data[idx][3]
                # drop mostly transparent pixels
                if (a < 200):
                    continue
                #print("r g b a: %d %d %d %d" % (r,g,b,a))
                rgb = "%02x%02x%02x" % (r, g, b)
                yield Pixel(x, y, rgb)
