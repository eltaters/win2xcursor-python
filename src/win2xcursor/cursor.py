"""Cursorfile generation module."""

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
        sizes: List of resolutions supported by this cursor.
        frames_list: Raw frames for each resolution.
        frames_dir: Directory to store required frames.
        ani: Ani file metadata.

    """

    def __init__(
        self,
        ani: AniData,
        frames_dir: pathlib.Path,
    ):
        """
        Create an instance object of this class.

        Args:
            ani: ANI file metadata.
            frames_dir: Directory to store required frames.

        """
        self.frames_dir: pathlib.Path = frames_dir
        self.sizes: list[int] = []
        self.frames_list: list[Frames] = []
        self.ani: AniData = ani

    def add(self, frames_list: list[Frames]) -> None:
        """
        Add a set of new resolutions to this cursor.

        Prioritizes repeated resolutions following FCFS priority.

        Args:
            frames_list: New resolutions to add.

        """
        sizes = set()
        for frames in frames_list:
            if frames.size in self.sizes:
                continue
            self.frames_list.append(frames)
            sizes.add(frames.size)

        self.sizes += sizes

    def buffer(self) -> str:
        """Create a string representation of the `.cursor` file."""
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
        Write the `.cursor` file with all specified resolutions.

        Also saves the frames that compose the cursor.

        Args:
            file: Output path for the .cursor file.

        """
        for frames in self.frames_list:
            for frame, name in zip(frames.images, frames.names):
                frame.save(self.frames_dir.joinpath(name), format="PNG")

        file.write_text(self.buffer())
