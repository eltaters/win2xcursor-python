import logging
import os
import pathlib

from win2xcursor.ani import AniData
from win2xcursor.frames import Frames

logger = logging.getLogger(__name__)
CURSOR_ENTRY_FMT = "{size} {x} {y} {path} {rate}\n"


class Cursor:
    """
    Wrapper class to generate .cursor from ANI.

    Attributes:
        resolutions (list): List of resolutions supported by this cursor.
        cursor_file (Path): Output file for the cursor.
    """

    sizes: list[Frames]
    file: pathlib.Path

    def __init__(
        self,
        ani: AniData,
        frames_dir: pathlib.Path,
        output_file: pathlib.Path,
    ):
        """
        Constructor method for this class.

        Args:
            ani (AniData): Ani file metadata.
            frames_dir (Path): Directory to store required frames.
            output_file (Path): Output path for the .cursor file.
        """
        self.frames_dir = frames_dir
        self.file = output_file
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

    def save(self):
        """
        Writes the .cursor file with all specified resolutions.
        """
        for size in self.sizes:
            for frame, name in zip(size.images, size.frame_names):
                frame.save(self.frames_dir.joinpath(name))

        self.file.write_text(self.buffer())
