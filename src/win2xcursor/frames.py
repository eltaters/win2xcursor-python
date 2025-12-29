"""Frame extraction and scaling module."""

from __future__ import annotations

from typing import NamedTuple

from PIL import Image, ImageOps

from win2xcursor.ico import IconDir, dib2png


class Frames(NamedTuple):
    """
    Representation of the frames that compose a cursor configuration.

    A .cursor file can have multiple configurations, one for each supported
    resolution.

    Attributes:
        images: List of frames.
        frame_names: Indexed name for each frame.
        hotspot_x: X offset for the configuration.
        hotspot_y: Y offset for the configuration.

    """

    images: list[Image.Image]
    names: list[str]
    hotspot_x: int
    hotspot_y: int

    @property
    def size(self) -> int:
        """Return the shared resolution of these frames."""
        return self.images[0].width


class FrameScaler:
    """
    Manager object for a series of frames in ICO format.

    Converts ICO files to PNG upon initialization and allows arbitrary scaling
    via the Nearest-Neighbor algorithm.

    Attributes:
        name: Name of original resource, which is then decomposed into frames.
        images: PNG representation of the frames.
        x: Base X hotspot for the frames.
        y: Base Y hotspot for the frames.

    """

    def __init__(self, icos: list[bytes], name: str, ignore_hotspots: bool):
        """
        Create an instance object of this class.

        Args:
            icos: List of ICO or CUR formatted buffers.
            name: Name of the original resource.
            ignore_hotspots: Sets X/Y hotspot values to 0 if True.

        """
        self.name = name
        self.resolutions = {}
        self.hotspots = {}

        for ico in icos:
            meta = IconDir.from_buffer(ico, ignore_hotspots)

            # Save every resolution
            for entry in meta.entries:
                self.resolutions.setdefault(entry.width, []).append(
                    dib2png(ico[entry.offset : entry.offset + entry.bytes])
                )
                self.hotspots[entry.width] = (entry.x, entry.y)

    def get_frames(self, scale_value: int) -> list[Frames]:
        """
        Scale the stored frames on a specified scale.

        Args:
            scale_value: scaling factor for the image:

        Returns:
            Scaled PNG frames alongside metadata in a Frames tuple.

        """
        frames_list = []
        for size in self.resolutions:
            images = [
                ImageOps.scale(image, scale_value, Image.Resampling.NEAREST)
                if scale_value > 1
                else image
                for image in self.resolutions[size]
            ]

            image_count = len(images)
            image_count_digits = len(str(image_count))
            index_width = max(image_count_digits, 2)
            indices = [
                str(i).zfill(index_width) for i in range(1, image_count + 1)
            ]

            frames_list.append(
                Frames(
                    images=images,
                    names=[
                        f"{self.name}{i}_{size}x{size}x{scale_value}.png"
                        for i in indices
                    ],
                    hotspot_x=self.hotspots[size][0] * scale_value,
                    hotspot_y=self.hotspots[size][1] * scale_value,
                )
            )

        return frames_list
