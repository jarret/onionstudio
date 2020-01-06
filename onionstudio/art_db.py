# Copyright (c) 2020 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php
import os
import time
import mmap


PIXEL_RECORD_BIT_SIZE = 12
BITS_PER_BYTE = 8

WIDTH = 1024
HEIGHT = 1024


class ArtDb(object):
    def __init__(self, art_db_dir):
        if not os.path.exists(art_db_dir):
            os.makedirs(art_db_dir)
        self.art_db_dir = art_db_dir
        self.n_pixels = WIDTH * HEIGHT
        self.size = ArtDb.total_bytes()
        self.mmap_art_bin()

    def total_bytes():
        total_pixels = WIDTH * HEIGHT
        total_bits = total_pixels * PIXEL_RECORD_BIT_SIZE
        assert total_bits % BITS_PER_BYTE == 0
        return total_bits // BITS_PER_BYTE

    def art_path(self):
        return os.path.join(self.art_db_dir, "studio.dat")

    def update_log_path(self):
        return os.path.join(self.art_db_dir, "updates.log")

    ###########################################################################

    def mmap_file_init(self, path):
        file_ref = open(path, "wb")
        file_ref.write(bytearray(0xff.to_bytes(1, byteorder='big') * self.size))
        file_ref.close()

    ###########################################################################

    def mmap_art_bin(self):
        path = self.art_path()
        if not os.path.exists(path):
            self.mmap_file_init(path)
        self.file_ref = open(path, "r+b")
        self.bin = mmap.mmap(self.file_ref.fileno(), self.size)

    def unmap_art_bin(self):
        self.bin.flush()
        self.bin.close()
        self.file_ref.close()

    def log_payload(self, payload):
        path = self.update_log_path()
        s = "%0.4f payload %s\n" % (time.time(), payload)
        f = open(path, "a")
        f.write(s)
        f.close()

    def map_bit(self, x, y):
        return ((x * PIXEL_RECORD_BIT_SIZE * HEIGHT) +
                (y * PIXEL_RECORD_BIT_SIZE))

    def read_rgb(self, x, y):
        bit = self.map_bit(x, y)
        front_aligned = (bit % BITS_PER_BYTE) == 0
        byte = bit // BITS_PER_BYTE
        value = int.from_bytes(self.bin[byte:byte + 2], byteorder="big")
        if front_aligned:
            rgb_value = (value >> 4) & 0x0fff
        else:
            rgb_value = value & 0x0fff
        print("read at %d: %03x" % (byte, rgb_value))
        return "%03x" % rgb_value

    def write_rgb(self, x, y, rgb):
        bit = self.map_bit(x, y)
        front_aligned = (bit % BITS_PER_BYTE) == 0
        byte = bit // BITS_PER_BYTE
        rgb_value = int("0" + rgb, 16)
        value = int.from_bytes(self.bin[byte:byte + 2], byteorder="big")
        print("read to update: %04x" % value)
        if front_aligned:
            value = (value & 0x000f) | (rgb_value << 4)
        else:
            value = (value & 0xf000) | rgb_value
        value_bin = value.to_bytes(2, byteorder="big")
        self.bin[byte:byte + 2] = value_bin
        print("wrote at %d: %s" % (byte, value_bin.hex()))

    def record_pixels(self, payload, pixels):
        for p in pixels:
            print("writing: %d %d = %s" % (p.x, p.y, p.rgb))
            self.write_rgb(p.x, p.y, p.rgb)
            assert self.read_rgb(p.x, p.y) == p.rgb
        self.log_payload(payload)
        self.bin.flush()

    def to_bin(self):
        return bytes(self.bin)
