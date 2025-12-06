"""Image extraction and conversion from ICO."""

from __future__ import annotations

import struct

from msgspec import Struct
from PIL import Image


class IconDir(Struct):
    """
    Represents the ICONDIR struct in an `ico` buffer.

    Attributes:
        reserved: Must be 0.
        type: 1 for ICO, 2 for CUR.
        count: Number of images in the file.
        entries: Each entry represents an image.

    """

    reserved: int
    type: int
    count: int
    entries: list[IconDirEntry]

    @classmethod
    def from_buffer(cls, buf: bytes, ignore_hotspots: bool = False):
        """
        Create an instance for this class from a buffer.

        Args:
            buf: Source data.
            ignore_hotspots: Sets x/y hotspot values of each entry to 0
            if True. Defaults to False.

        """
        reserved, type_, count = struct.unpack_from("<3H", buf, 0)
        entries = [
            IconDirEntry.from_buffer(
                buf[6 + i * 16 : 6 + (i + 1) * 16],
                ignore_hotspots or type_ == 1,
            )
            for i in range(count)
        ]
        return cls(reserved=reserved, type=type_, count=count, entries=entries)


class IconDirEntry(Struct):
    """
    Represents an entry inside the `ICONDIR` struct.

    Attributes:
        width: Image width.
        height: Image height.
        color_count: Color palette.
        reserved: Must be 0.
        x: Color planes in ICO, x hotspot in CUR.
        y: Bits per pixel in ICO, y hotspot in CUR.
        bytes: Image size in bytes
        offset: Offset of BMP/PNG data from the ICO/CUR file.

    """

    width: int
    height: int
    color_count: int
    reserved: int
    x: int
    y: int
    bytes: int
    offset: int

    @classmethod
    def from_buffer(cls, buf: bytes, ignore_hotspots: bool = False):
        """
        Create an instance of this class from a buffer.

        Args:
            buf: Source data.
            ignore_hotspots: Sets X/Y hotspot values to 0 if True.
            Defaults to False.

        """
        instance = cls(*struct.unpack_from("<4B2H2I", buf, 0))
        instance.x, instance.y = (
            (0, 0) if ignore_hotspots else (instance.x, instance.y)
        )
        return instance


class BitmapInfoHeader(Struct):
    """
    Represents metadata for a bitmap.

    Extracted from: https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapinfoheader.
    Only the size, width and height attributes are used.

    Attributes:
        size: Size of this header. Always 40.
        width: Width of the bitmap in pixels.
        height: Height of the bitmap in pixels, adjusted for the mask.

    """

    size: int
    width: int
    _height: int
    planes: int
    bit_count: int
    compression: int
    size_image: int
    x_pels_per_meter: int
    y_pels_per_meter: int
    color_used: int
    color_important: int

    @classmethod
    def from_buffer(cls, buf: bytes) -> BitmapInfoHeader:
        """
        Create an instance for this class from a buffer.

        Args:
            buf: Source data.

        """
        instance = cls(*struct.unpack_from("<3I2H6I", buf, 0))
        assert instance.size == struct.calcsize("<3I2H6I")
        return instance

    @property
    def height(self) -> int:
        """The patched height for this bitmap."""
        return self._height // 2


def dib2png(data: bytes) -> Image.Image:
    """Convert a DIB from an ICO file to PNG, applying the AND mask."""
    header = BitmapInfoHeader.from_buffer(data)

    # Compute strides (extracted from microsoft docs)
    row_bytes = ((header.width * header.bit_count + 31) & ~31) >> 3
    mask_row_bytes = ((header.width + 31) & ~31) >> 3

    # Split pixels and mask
    img = Image.frombuffer(
        "RGBA",
        (header.width, header.height),
        data[header.size : header.size + row_bytes * header.height],
        "raw",
        "BGRA",  # decoder mode
        row_bytes,  # stride
        -1,  # flip image
    )

    alpha = Image.frombuffer(
        "1",  # one bit per pixel
        (header.width, header.height),
        data[header.size + row_bytes * header.height :],
        "raw",
        "1;I",
        mask_row_bytes,
        -1,
    ).convert("L")

    # Apply the mask
    img.putalpha(alpha)
    return img
