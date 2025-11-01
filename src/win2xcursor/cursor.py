import logging
import os
import pathlib
import struct
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps

from win2xcursor.ani import AniData

logger = logging.getLogger(__name__)

CURSOR_ENTRY_FMT = "{size} {x} {y} {path} {rate}\n"


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

    return images, (x * scale, y * scale), images[0].width


class Cursor:
    """
    Wrapper class to generate .cursor from ANI.

    Attributes:
        dry (bool): Whether the generator is being run in dry mode.
                    Regular mode saves any PNG images it saves from ANI files.
                    Dry mode does not save the images.
        framedir (Path): Location to store frames at.
    """

    def __init__(self, framedir: pathlib.Path, dry: bool):
        self.dry = dry
        self.framedir = framedir

    def from_ani(self, ani_file: pathlib.Path, scale: int) -> str:
        """
        Generates a .cursor buffer from an ani file.

        Args:
            ani_file (Path): ANI file location.
            scale (int): Scaling applied to the extracted PNGs.

        Returns:
            str: xcursor file as a buffer.

        """

        buffer = ""
        imgpaths = []
        ani = AniData(ani_file)
        images, (x, y), width = ico2png(ani.frames, scale)

        logger.debug(f"File metadata for {ani_file!s}")
        logger.debug(ani.header)

        # Create relative image paths
        for i in range(ani.header.frames):
            index = str(i + 1).zfill(len(str(ani.header.frames)))
            imgpaths.append(
                self.framedir.joinpath(f"{ani_file.stem}{index}.png")
            )

        # Write the buffer
        for i, rate, path in zip(ani.sequence, ani.rates, imgpaths):
            buffer += CURSOR_ENTRY_FMT.format(
                size=width,
                x=x,
                y=y,
                path=os.path.sep.join(path.parts[-2:]),
                rate=rate,
            )

        if self.dry is True:
            return buffer

        # Regular mode only: store the images
        for img, path in zip(images, imgpaths):
            img.save(path)

        return buffer
