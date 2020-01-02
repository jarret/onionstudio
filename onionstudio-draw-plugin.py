#!/usr/bin/env python3
import os
from pyln.client import Plugin

from onionstudio.pixel import Pixel
from onionstudio.manual import ManualToPixels
from onionstudio.png import PngToPixels
from onionstudio.draw import Draw


plugin = Plugin()

@plugin.init()
def init(options, configuration, plugin, **kwargs):
    node = plugin.get_option("onion_studio_node")
    plugin.log("initialzed to draw to %s" % node)


###############################################################################

def parse_pixel_args(pixels_string):
    pixels, err = ManualToPixels(pixels_string)
    if err:
        return None, None, err
    return pixels, None

@plugin.method("os_draw_pixels")
def draw_pixels(plugin, pixels):
    """Draws manually-specified pixels to Onion Studio at the cost of 1
       satoshi per pixel

        pixels - is a string that specifies the x,y cordinates and RGB colors
            eg. 1_1_ffffff will set the pixel at coordinate at (1, 1) to
                white #ffffff
                1_1_00ff00_2_2_00ff00 will set the pixels at coordinates
                (1, 1) and (2,2) to green #00ff00
    """
    pixels, err = parse_pixel_args(pixels)
    if err:
        return err
    plugin.log("pixels: %s" % [str(p) for p in pixels])
    node = plugin.get_option("onion_studio_node")
    d = Draw(plugin.rpc, node, pixels)
    err = d.run()
    if err:
        return err
    return "finished drawing %d pixels" % len(pixels)

###############################################################################

def parse_png_args(x_offset_string, y_offset_string, png_filename):
    try:
        x_offset = int(x_offset_string)
        y_offset = int(y_offset_string)
    except:
        return None, None, "could not parse args"
    if not os.path.exists(png_filename):
        return None, None, None, None, "no file at path: %s" % png_filename
    if not png_filename.endswith(".png"):
        return None, None, None, None, "not a png file: %s" % png_filename
    return x_offset, y_offset, png_filename, None

@plugin.method("os_draw_png")
def draw_png(plugin, x_offset, y_offset, png_filename):
    """ Draws a png image file to Onion Studio placed with the top corner at
        the given x and y offset. It will be drawn at a cost of 1 satoshi per
        pixel. The color space will be clamped to the 12-bit colorspace that
        Onion Studio requires.  Transparent pixels in the image will be
        ignored.
        x_offset = the x coordinate to place the image
        y_offset = the y coordinate to place the image
        png_filename = the path to a .png file to use as the source image
    """
    x_offset, y_offset, png_filename, err = parse_png_args(x_offset, y_offset,
                                                           png_filename)
    if err:
        return err

    pp = PngToPixels(png_filename)
    pixels = list(pp.iter_at_offset(x_offset, y_offset))
    node = plugin.get_option("bannerpunk_node")
    d = Draw(plugin.rpc, node, pixels)
    err = d.run()
    if err:
        return err
    return "finished drawing %d pixels" % len(pixels)

###############################################################################

# the "offical" onion studio node
NODE = "02e389d861acd9d6f5700c99c6c33dd4460d6f1e2f6ba89d1f4f36be85fc60f8d7"

plugin.add_option("onion_studio_node", NODE,
                  "the node we are paying to draw to")
plugin.run()
