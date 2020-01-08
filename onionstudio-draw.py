#!/usr/bin/env python3
# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import os
import sys
import argparse

from onionstudio.draw import Draw
from onionstudio.png import PngToPixels
from onionstudio.manual import ManualToPixels

from pyln.client import LightningRpc

# the "offical" onion studio node
NODE = "02e389d861acd9d6f5700c99c6c33dd4460d6f1e2f6ba89d1f4f36be85fc60f8d7"

PNG_PIXEL_SAFETY = 1000

###############################################################################

def manual_func(s, rpc):
    ap = ManualToPixels(s.pixels)
    pixels, err = ap.parse_pixels()
    if err:
        return None, err
    d = Draw(rpc, NODE, pixels)
    report, err = d.run()
    return report, err

def png_func(s, rpc):
    try:
        from PIL import Image
    except:
        return None, ("\n*** couldn't find pillow library dependency for png images\n"
                      "try:\n"
                      "  $ sudo apt-get install libopenjp2-7 libtiff5\n"
                      "  $ sudo pip3 install pillow")
    if not os.path.isfile(s.png_file):
        return None, "no such file? %s" % s.png_file

    pp = PngToPixels(s.png_file)
    pixels = list(pp.iter_at_offset(s.x_offset, s.y_offset))[s.resume_at_px:]
    if not s.big and len(pixels) > PNG_PIXEL_SAFETY:
        return None, ("*** This will draw %d pixels at a cost of %d satoshis, "
                      "which is a lot so we want to make sure you actually intend "
                      "to spend that amount. To proceed with this, please use the "
                      "--big cli option.") % (len(pixels), len(pixels))

    #pixels = pixels[0 - (2 * len(pixels) // 3):] # hack to continue failed drawing
    d = Draw(rpc, NODE, pixels)
    report, err = d.run()
    return report, err

###############################################################################

parser = argparse.ArgumentParser(prog="onion-draw.py")
parser.add_argument("lightning_rpc", type=str,
                    help="path to your c-lightning rpc file for sending calls")

subparsers = parser.add_subparsers(title='subcommands',
                                   description='selects style of drawing',
                                   help='manually enter pixels or use .png')

manual = subparsers.add_parser('manual', help="draw manually specified pixels")
png = subparsers.add_parser('png',
                            help="draw from a provided .png file "
                                 "(requires that you install pillow "
                                 "and dependencies)")

manual.add_argument('pixels', type=str,
                    help="a string specifying coordinates and colors of "
                         "pixels to draw separated by underscores. "
                         "Eg. 1_1_fff_2_2_0f0 will set pixel "
                         "(1,1) white (#fff) and (2,2) green (#0f0)")
manual.set_defaults(func=manual_func)

png.add_argument("x_offset", type=int,
                 help="the x coordinate to begin drawing at")
png.add_argument("y_offset", type=int,
                 help="the y coordinate to begin drawing at")
png.add_argument("png_file", type=str, help="the path to the png file to use")
png.add_argument("-b", "--big", action="store_true",
                 help="acknowledge that this is a big spend and proceed anyway")
png.add_argument("-r", "--resume-at-px", type=int, default=0,
                 help="resume the drawing at a this pixels. useful if a draw "
                      "is interrupted midway")
png.set_defaults(func=png_func)

settings = parser.parse_args()

if not os.path.exists(settings.lightning_rpc):
    sys.exit("*** no such file? %s" % settings.lightning_rpc)

if not hasattr(settings, "func"):
    sys.exit("*** must specify either 'manual' or 'png' mode")

rpc = LightningRpc(settings.lightning_rpc)

report, err = settings.func(settings, rpc)
if report:
    print("drew %d out of %d pixels" % (report['pixels_drawn'],
                                        report['total_pixels']))
    if report['pixels_drawn'] != report['total_pixels']:
        resume_from = settings.resume_at_px + report['pixels_drawn']
        print("To attempt to resume the draw from wher it failed, call again "
              "with  '--resume-at-px %d' at the end." % resume_from)
if err:
    sys.exit(err)

