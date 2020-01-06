#!/usr/bin/env python3
# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import os
from pyln.client import Plugin

from onionstudio.pixel import Pixel
from onionstudio.manual import ManualToPixels
from onionstudio.png import PngToPixels
from onionstudio.draw import Draw

# the "offical" onion studio node
NODE = "02e389d861acd9d6f5700c99c6c33dd4460d6f1e2f6ba89d1f4f36be85fc60f8d7"

PNG_PIXEL_SAFETY = 1000

CATEGORY = "Onion Studio"

###############################################################################

plugin = Plugin()

@plugin.init()
def init(options, configuration, plugin, **kwargs):
    node = plugin.get_option("onion_studio_node")
    plugin.log("initialzed to draw to %s" % node)


###############################################################################

MANUAL_DESC = "Draw manually-specified pixels."

MANUAL_LONG_DESC = """
Draws manually-specified pixels to Onion Studio at the cost of 1
satoshi per pixel.

pixels - is a string that specifies the x,y cordinates and RGB colors.
    Eg.
        1_1_fff will set the pixel at coordinate at (1, 1) to
        white #fff

        1_1_0f0_2_2_0f0 will set the pixels at coordinates
        (1, 1) and (2,2) to green #0f0
"""

def parse_pixel_args(pixels_string):
    mp = ManualToPixels(pixels_string)
    pixels, err = mp.parse_pixels()
    if err:
        return None, err
    return pixels, None

@plugin.method("os_draw_manual", category=CATEGORY, desc=MANUAL_DESC,
               long_desc=MANUAL_LONG_DESC)
def draw_manual(plugin, pixels):
    pixels, err = parse_pixel_args(pixels)
    if err:
        return err
    plugin.log("pixels: %s" % [str(p) for p in pixels])
    node = plugin.get_option("onion_studio_node")
    d = Draw(plugin.rpc, node, pixels)
    report, err = d.run()
    if report:
        report = "drew %d out of %d pixels" % (report['pixels_drawn'],
                                               report['total_pixels'])
    if err:
        return err if not report else report + "\n" + err
    return report

###############################################################################

PNG_DESC = ("Draws pixels sourced from a .png image placed at a chosen "
            "coordinate")

PNG_LONG_DESC = """
Draws a png image file to Onion Studio placed with the top left corner at the
given x and y offset. It will be drawn at a cost of 1 satoshi per pixel. The
color space will be clamped to the 12-bit colorspace that Onion Studio
requires. Transparent pixels in the image will not be drawn.

    x_offset = the x coordinate to place the image.

    y_offset = the y coordinate to place the image.

    png_filename = the path to a .png file to use as the source image.

    big = provide the string 'big' to opt in to allowing large amounts of
        pixels to be bought with one invocation of this command.

    resume_at_px = a pixel number in the list of pixels to resume a drawing
        operation. Allows easy continuation if a previous mult-part drawing
        operation fails midway.
"""

def parse_png_args(x_offset_string, y_offset_string, png_filename):
    png_filename = os.path.abspath(png_filename)
    try:
        x_offset = int(x_offset_string)
        y_offset = int(y_offset_string)
    except:
        return None, None, "could not parse args"
    if not os.path.isfile(png_filename):
        return None, None, None, "no file at path: %s" % png_filename
    if not png_filename.endswith(".png"):
        return None, None, None, "not a png file: %s" % png_filename
    return x_offset, y_offset, png_filename, None

@plugin.method("os_draw_png", category=CATEGORY, desc=PNG_DESC,
               long_desc=PNG_LONG_DESC)
def draw_png(plugin, x_offset, y_offset, png_filename, big="", resume_at_px=0):
    x_offset, y_offset, png_filename, err = parse_png_args(x_offset, y_offset,
                                                           png_filename)
    if err:
        return err

    pp = PngToPixels(png_filename)
    pixels = list(pp.iter_at_offset(x_offset, y_offset))[resume_at_px:]

    if big != "big" and len(pixels) > PNG_PIXEL_SAFETY:
        return ("*** This will draw %d pixels at a cost of %d satoshis, "
                "which is a lot so we want to make sure you actually intend "
                "to spend that amount. To proceed with this, please append the "
                "word 'big' at the end of the command") % (len(pixels),
                                                           len(pixels))
    node = plugin.get_option("onion_studio_node")
    d = Draw(plugin.rpc, node, pixels)
    report, err = d.run()
    if report:
        report = "drew %d out of %d pixels" % (report['pixels_drawn'],
                                               report['total_pixels'])
    if err:
        return err if not report else report + "\n" + err
    return report

###############################################################################


plugin.add_option("onion_studio_node", NODE,
                  "the node we are paying to draw to")
plugin.run()
