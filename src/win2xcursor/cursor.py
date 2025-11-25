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

    frames_list: list[Frames]
    sizes: list[int]
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
        self.frames_list = []
        self.ani = ani

    def add(self, frames_list: list[Frames]) -> None:
        """
        Adds a new resolution to this cursor.

        Args:
            scale (int): Scaling applied to the extracted PNGs.
        """
        sizes = set()
        for frames in frames_list:
            if frames.size in self.sizes:
                continue
            self.frames_list.append(frames)
            sizes.add(frames.size)

        self.sizes += sizes

    def buffer(self) -> str:
        """
        Returns the text that will be written to the `.cursor` file.
        """
        buffer = ""

        for frames in self.frames_list:
            for i, rate in zip(self.ani.sequence, self.ani.rates):
                buffer += CURSOR_ENTRY_FMT.format(
                    size=frames.size,
                    x=frames.hotspot_x,
                    y=frames.hotspot_y,
                    path=os.path.sep.join(
                        [self.frames_dir.name, frames.names[i]]
                    ),
                    rate=rate,
                )

        return buffer

    def save(self, file: pathlib.Path) -> None:
        """
        Writes the .cursor file with all specified resolutions.

        Args:
            file (Path): Output path for the .cursor file.
        """

        for frames in self.frames_list:
            for frame, name in zip(frames.images, frames.names):
                frame.save(self.frames_dir.joinpath(name), format="PNG")

        file.write_text(self.buffer())
