# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import struct
import zlib

from .winapi import _BIH, _vp, gdi, shl, u32


def _png(w, h, rgb):
    raw = b"".join(
        b"\x00" + rgb[y * w * 3:(y + 1) * w * 3]
        for y in range(h)
    )

    def ch(t, d):
        return (
            struct.pack(">I", len(d)) + t + d
            + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + ch(b"IDAT", zlib.compress(raw))
        + ch(b"IEND", b"")
    )


def _icon_png(path, size, bg):
    big = _vp()

    if (
        shl.ExtractIconExW(
            path, 0, ctypes.byref(big), None, 1
        ) < 1
        or not big.value
    ):
        return None

    hdc = u32.GetDC(None)
    mdc = gdi.CreateCompatibleDC(hdc)

    bih = _BIH(
        ctypes.sizeof(_BIH), size, -size,
        1, 32, 0, 0, 0, 0, 0, 0
    )

    bits = _vp()

    bmp = gdi.CreateDIBSection(
        mdc, ctypes.byref(bih), 0,
        ctypes.byref(bits), None, 0
    )

    png = None

    if bmp and bits.value:
        old = gdi.SelectObject(mdc, bmp)

        px = bytes((bg[2], bg[1], bg[0], 255)) * (size * size)
        ctypes.memmove(bits.value, px, len(px))

        u32.DrawIconEx(mdc, 0, 0, big, size, size, 0, None, 3)

        raw = ctypes.string_at(bits.value, size * size * 4)

        rgb = bytearray(size * size * 3)
        rgb[0::3] = raw[2::4]
        rgb[1::3] = raw[1::4]
        rgb[2::3] = raw[0::4]

        png = _png(size, size, bytes(rgb))
        gdi.SelectObject(mdc, old)

    if bmp:
        gdi.DeleteObject(bmp)

    gdi.DeleteDC(mdc)
    u32.ReleaseDC(None, hdc)
    u32.DestroyIcon(big)

    return png
