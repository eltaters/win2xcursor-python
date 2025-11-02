import logging
import os
import pathlib

from win2xcursor.ani import AniData
from win2xcursor.frames import Frames

logger = logging.getLogger(__name__)
CURSOR_ENTRY_FMT = "{size} {x} {y} {path} {rate}\n"


class CursorFile:
    """
    Wrapper class to generate .cursor from ANI.

    Attributes:
        sizes (list): List of resolutions supported by this cursor.
        frames_dir (Path): Directory to store required frames.
        ani (AniData): Ani file metadata.
    """

    sizes: list[Frames]
    frames_dir: pathlib.Path
    ani: AniData

    def __init__(
        self,
        ani: AniData,
        frames_dir: pathlib.Path,
    ):
        """
        Constructor method for this class.

        Args:
            ani (AniData): Ani file metadata.
            frames_dir (Path): Directory to store required frames.
        """
        self.frames_dir = frames_dir
        self.sizes = []
        self.ani = ani

    def add(self, frames: Frames):
        """
        Adds a new resolution to this cursor.

        Args:
            scale (int): Scaling applied to the extracted PNGs.
        """
        self.sizes.append(frames)

    def buffer(self) -> str:
        """
        Returns the buffer representation that will be written on the .cursor
        file.
        """
        buffer = ""

        for frames in self.sizes:
            for i, rate in zip(self.ani.sequence, self.ani.rates):
                buffer += CURSOR_ENTRY_FMT.format(
                    size=frames.size,
                    x=frames.hotspot_x,
                    y=frames.hotspot_y,
                    path=os.path.sep.join(
                        [self.frames_dir.name, frames.frame_names[i]]
                    ),
                    rate=rate,
                )

        return buffer

    def save(self, file: pathlib.Path):
        """
        Writes the .cursor file with all specified resolutions.

        Args:
            file (Path): Output path for the .cursor file.
        """
        for size in self.sizes:
            for frame, name in zip(size.images, size.frame_names):
                frame.save(self.frames_dir.joinpath(name))

        file.write_text(self.buffer())
