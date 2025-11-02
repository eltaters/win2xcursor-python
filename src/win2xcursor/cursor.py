import logging
import os
import pathlib
import struct
from typing import NamedTuple
from msgspec import Struct
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps

from win2xcursor.ani import AniData

logger = logging.getLogger(__name__)
CURSOR_ENTRY_FMT = "{size} {x} {y} {path} {rate}\n"


class ImageData(Struct):
    """
    Represents data from a set of PNG frames used to create
    a cursor.

    Attributes:
        images (list): List of images with shared metadata.
        x (int): X hotspot coordinate.
        y (int): Y hotspot coordinate.
        scale (int): Scaling multiplier applied to the image.
    """

    images: list[Image.Image]
    x: int
    y: int
    scale: int

    @property
    def size(self) -> int:
        """int: size of the image"""
        return self.images[0].width

    def indexed_names(self, base_name: str) -> list[str]:
        """
        Wrapper to assign a filename index to every image in the struct.

        Args:
            base_name (str): Name of the original ANI file.

        Returns:
            list: Indexed names of every frame.
        """

        names = []

        for i in range(len(self.images)):
            index = str(i + 1).zfill(max(2, len(str(len(self.images)))))
            names.append(f"{base_name}{index}x{self.scale}.png")

        return names


class Resolution(NamedTuple):
    """Cursor resolution representation"""

    image_data: ImageData
    file_names: list[str]


def ico2png(icos: list[bytes], scale: int = 1):
    """
    Transforms a list of .ico buffers into PNG images.

    Args:
        icos (list): list of ICO buffers.

    Returns:
        tuple: .png buffers, x/y hotspot
    """

    # Check .ico type -> 2 contains X/Y offsets
    if (struct.unpack_from("<H", icos[0], 2)[0]) != 2:
        x, y = 0, 0
    else:
        x, y = struct.unpack_from("<HH", icos[0], 10)

    images = []

    for ico in icos:
        with Image.open(BytesIO(ico)) as img:
            img = img.convert("RGBA")
            pixels = np.array(img)

            # HACK: black pixel: usually a bg pixel from RGB images
            r, g, b, _ = pixels.T
            black_areas = (r <= 0) & (g <= 0) & (b <= 0)
            pixels[..., 3][black_areas.T] = 0

            img = Image.fromarray(pixels)
            if scale > 1:
                img = ImageOps.scale(img, scale, Image.Resampling.NEAREST)

            images.append(img)

    return ImageData(images, x * scale, y * scale, scale)


class Cursor:
    """
    Wrapper class to generate .cursor from ANI.

    Attributes:
        resolutions (list): List of resolutions supported by this cursor.
        cursor_file (Path): Output file for the cursor.
    """

    resolutions: list[Resolution]
    cursor_file: pathlib.Path

    def __init__(
        self,
        ani_file: pathlib.Path,
        frames_dir: pathlib.Path,
        cursor_dir: pathlib.Path,
    ):
        self.ani_file = ani_file
        self.frames_dir = frames_dir
        self.cursor_file = cursor_dir.joinpath(f"{ani_file.stem}.cursor")
        self.resolutions = []

        self.ani = AniData.from_file(ani_file)
        logger.debug(f"File metadata for {ani_file!s}")
        logger.debug(self.ani.header)

    def add(self, scale: int):
        """
        Adds a new resolution to this cursor.

        Args:
            scale (int): Scaling applied to the extracted PNGs.
        """
        images = ico2png(self.ani.frames, scale)
        self.resolutions.append(
            Resolution(images, images.indexed_names(self.ani_file.stem))
        )

    def buffer(self) -> str:
        """
        Returns the buffer representation that will be written on the .cursor
        file.
        """
        buffer = ""

        for r in self.resolutions:
            for i, rate in zip(self.ani.sequence, self.ani.rates):
                buffer += CURSOR_ENTRY_FMT.format(
                    size=r.image_data.size,
                    x=r.image_data.x,
                    y=r.image_data.y,
                    path=os.path.sep.join(
                        [self.frames_dir.name, r.file_names[i]]
                    ),
                    rate=rate,
                )

        return buffer

    def save(self):
        """
        Writes the .cursor file with all specified resolutions.
        """
        for r in self.resolutions:
            for img, path in zip(r.image_data.images, r.file_names):
                img.save(self.frames_dir.joinpath(path))

        self.cursor_file.write_text(self.buffer())
