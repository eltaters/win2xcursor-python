import struct
from io import BytesIO
from typing import NamedTuple

import numpy as np
from PIL import Image, ImageOps


class Frames(NamedTuple):
    """
    Representation of the frames that compose a cursor configuration.
    A .cursor file can have multiple configurations, one for each supported
    resolution.

    Attributes:
        images  (list): List of frames.
        frame_names (list): Indexed name for each frame.
        hotspot_x: X offset for the configuration.
        hotspot_y: Y offset for the configuration.
    """

    images: list[Image.Image]
    frame_names: list[str]
    hotspot_x: int
    hotspot_y: int

    @property
    def size(self) -> int:
        """
        int: Shared resolution size of the frames, which have the same width
        and height.
        """
        return self.images[0].width


class FrameScaler:
    """
    Manager object for a series of frames in ICO format. Converts ICO files to
    png upon initialization and allows arbitrary scaling via NN.

    Attributes:
        name (str): Name of the original resource, which is then decomposed
                    into frames.
        images (Image.Image): PNG representation of the frames.
        x (int): Base x hotspot for the frames.
        y (int): Base y hotspot for the frames.

    """

    def __init__(self, icos: list[bytes], name: str, ignore_hotspots: bool):
        """
        Constructor for this class. Converts ICO images into transparent PNGs.
        Currently considers pure black pixels (0,0,0) as part of the background
        and removes them.

        Args:
            icos (list): List of ICO or CUR formatted buffers.
            name (str): Name of the original resource.
        """
        self.name = name
        if ignore_hotspots or (struct.unpack_from("<H", icos[0], 2)[0]) != 2:
            self.x, self.y = 0, 0
        else:
            self.x, self.y = struct.unpack_from("<HH", icos[0], 10)

        self.images = []

        for ico in icos:
            with Image.open(BytesIO(ico)) as img:
                img = img.convert("RGBA")
                pixels = np.array(img)

                # Transform all black pixels to transparent
                r, g, b, _ = pixels.T
                black_areas = (r <= 0) & (g <= 0) & (b <= 0)
                pixels[..., 3][black_areas.T] = 0

                self.images.append(Image.fromarray(pixels))

    def get_frames(self, scale_value: int) -> Frames:
        """
        Scales the stored frames on a specified scale.

        Args:
            scale_value (int): scaling factor for the image:

        Returns:
            Frames: Scaled PNG frames alongside metadata in a Frames tuple.
        """
        images = []
        names = []
        for i, image in enumerate(self.images):
            image = (
                ImageOps.scale(image, scale_value, Image.Resampling.NEAREST)
                if scale_value > 1
                else image
            )

            index = str(i + 1).zfill(max(2, len(str(len(self.images)))))
            images.append(image)
            names.append(
                f"{self.name}{index}x{scale_value}.png",
            )

        return Frames(
            images=images,
            frame_names=names,
            hotspot_x=self.x * scale_value,
            hotspot_y=self.y * scale_value,
        )
