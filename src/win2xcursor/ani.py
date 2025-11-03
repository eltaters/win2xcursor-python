from __future__ import annotations

import logging
import pathlib
import struct
from typing import Any, Iterable

from msgspec import Struct

logger = logging.getLogger(__name__)


class AniHeader(Struct):
    """
    Represents the ANIHEADER struct in the `anih` chunk.

    Attributes:
        size (int): Length of this chunk.
        frames (int): Number of frames in the file.
        steps (int): Number of steps in the animation loop.
        cx (int): Not used.
        cy (int): Not used.
        bit_count (int): Not used.
        planes (int): Not used.
        jifrate (int): Display rate in milliseconds.
        fl (int): AF_SEQUENCE (0x2) | AF_ICON (0x1). AF_ICON should be set,
                  but AF_SEQUENCE is optional.
    """

    size: int
    frames: int
    steps: int
    cx: int
    cy: int
    bit_count: int
    planes: int
    _jifrate: int
    _fl: int

    @property
    def jifrate(self) -> int:
        """int: Default display rate, in milliseconds."""
        return int(1000 * self._jifrate / 60)

    @property
    def icon(self) -> bool:
        """bool: AF_ICON flag."""
        return self._fl & 0x1 != 0

    @property
    def sequence(self) -> bool:
        """bool: AF_SEQUENCE optional flag."""
        return self._fl & 0x2 != 0

    def __repr__(self) -> str:
        return (
            f"\tsize: {self.size}\n"
            f"\tframes: {self.frames}\n"
            f"\tsteps: {self.steps}\n"
            f"\tjifrate: {self.jifrate}\n"
            f"\tflags: AF_ICON {self.icon} AF_SEQUENCE {self.sequence}"
        )


class AniData:
    """
    Class representation for a windows .ANI file.

    Attributes:
        header (AniHeader): Header information for this file.
        sequence (list): Order of frames in the animation by index.
        rates (list): Jifrate per frame in the sequence.
        frames (list): Raw ICO buffers on the file.
    """

    _data: bytes
    _offset: int
    header: AniHeader
    sequence: list[int]
    rates: list[int]
    frames: list[bytes]

    def __init__(self, buffer: bytes):
        """
        Constructor method for this class.

        Args:
            buffer (bytes): ANI data.
        """
        self._data = buffer
        self._offset = 0

        # RIFF header validation
        ftype, size = self.unpack("<4sI")

        if ftype != b"RIFF":
            raise ValueError("Not a RIFF file")

        if size + 8 != len(self._data):
            raise ValueError(
                f"Expected file size {size + 8}, got {len(self._data)}"
            )

        # RIFF type
        rifftype, anih = self.unpack("<4s4s")
        if rifftype != b"ACON" or anih != b"anih":
            raise ValueError("Expected an .ani file")

        # ANIH data
        anihsize = self.unpack("<I")[0]
        self.header = AniHeader(*self.unpack("<9I"))

        assert anihsize == self.header.size, "Sizes differ"

        # File options
        self.sequence = self._sequence(self.header.sequence)
        self.rates = self._rates(self.header.sequence)
        self.frames = self._frames()

    @classmethod
    def from_file(cls, path: pathlib.Path) -> AniData:
        """
        Alternate constructor method from a file.

        Args:
            path (Path): ANI file path.

        Returns:
            AniData: instance constructed from path.
        """
        with open(path, "rb") as f:
            buffer = f.read()

        return cls(buffer=buffer)

    def unpack(self, format: str) -> tuple[Any, ...]:
        """
        Unpacks a set of values according to format.
        Automatically advances the internal offset by formatsize.

        Args:
            format (str): Unpacking format, according to the specifications of
                          the struct module.

        Returns:
            tuple: Unpacked values according to format.
        """
        values = struct.unpack_from(format, self._data, self._offset)
        self._offset += struct.calcsize(format)

        return values

    def findall(self, sub: bytes) -> Iterable[int]:
        """
        Generator method to find a bytearray in the file.

        Args:
            sub (bytes): bytearray to find.

        Yields:
            int: The next index where `sub` is located plus 4.

        Examples:
            >>> self._data = b"...LIST...LIST..."
            >>> print([i for i in self.findall(sub=b"LIST")
            [ 7, 14 ]
        """
        i = -1
        while (i := self._data.find(sub, i + 5)) != -1:
            yield i + 4

    def _sequence(self, af_sequence: bool) -> list[int]:
        """
        Computes the sequence list for this file.

        Args:
            af_sequence (bool): if the AF_SEQUENCE bit is on.

        Returns:
            list: Frame sequence indices.
        """
        if af_sequence is False:
            return list(range(self.header.frames))

        # Return the first valid candidate
        for offset in self.findall(b"seq"):
            self._offset = offset

            if self.unpack("<I")[0] / 4 != self.header.steps:
                continue

            seq = [self.unpack("<I")[0] for _ in range(self.header.steps)]

            if any(s > self.header.steps for s in seq):
                continue

            return seq

        return list(range(self.header.steps))

    def _rates(self, af_sequence: bool) -> list[int]:
        """
        Computes the rate for each frame in the sequence.

        Args:
            af_sequence (bool): if the AF_SEQUENCE bit is on.

        Returns:
            list: Frame sequence rates, in milliseconds.
        """
        count = self.header.steps if af_sequence else self.header.frames

        for offset in self.findall(b"rate"):
            self._offset = offset

            if self.unpack("<I")[0] / 4 != count:
                continue

            return [self.unpack("<I")[0] for _ in range(count)]

        return [self.header.jifrate] * count

    def _frames(self) -> list[bytes]:
        """
        Parses all ico files from the internal data buffer.

        Returns:
            list: Frames in the file, in ico format.
        """
        frames = []
        for offset in self.findall(b"LIST"):
            self._offset = offset
            _, ltype = self.unpack("<I4s")

            # Ignore other lists, such as "INFO"
            if ltype != b"fram":
                continue

            # Copy frame data
            for _ in range(self.header.frames):
                _, icolen = self.unpack("<4sI")
                frames.append(self._data[self._offset : self._offset + icolen])
                self._offset += icolen
            return frames

        return frames
