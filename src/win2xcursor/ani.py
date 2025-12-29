"""
Ani handling module.

Defines the structure of an ANI file, its header values and how its
metadata is extracted and treated.

"""

from __future__ import annotations

import logging
import pathlib
import struct
from typing import Any, Iterable

from msgspec import Struct

# Unit of measurement for a frame's display rate.
JIFFY = 1000 / 60

logger = logging.getLogger(__name__)


class AniHeader(Struct):
    """
    Represents the ANIHEADER struct in the `anih` chunk.

    Attributes:
        size: Length of this chunk.
        frames: Number of frames in the file.
        steps: Number of steps in the animation loop.
        cx: Not used.
        cy: Not used.
        bit_count: Not used.
        planes: Not used.
        jifrate: Display rate in milliseconds.
        fl: AF_SEQUENCE (0x2) | AF_ICON (0x1). AF_ICON should be set,
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

    @classmethod
    def from_buffer(cls, buffer: bytes) -> AniHeader:
        """Create an `AniHeader` from an in-memory buffer."""
        return cls(*struct.unpack_from("<9I", buffer))

    @property
    def jifrate(self) -> int:
        """Default display rate, in milliseconds."""
        return round(self._jifrate * JIFFY)

    @property
    def icon(self) -> bool:
        """AF_ICON flag."""
        return self._fl & 0x1 != 0

    @property
    def sequence(self) -> bool:
        """AF_SEQUENCE optional flag."""
        return self._fl & 0x2 != 0

    def __repr__(self) -> str:
        """Create a string representation of this object."""
        return (
            f"\tsize: {self.size}\n"
            f"\tframes: {self.frames}\n"
            f"\tsteps: {self.steps}\n"
            f"\tjifrate: {self.jifrate}\n"
            f"\tflags: AF_ICON {self.icon} AF_SEQUENCE {self.sequence}"
        )


class AniData:
    """
    Represents the parsed data within an ANI-formatted buffer.

    Attributes:
        header: Header information for this file.
        sequence: Order of frames in the animation by index.
        rates: Jifrate per frame in the sequence.
        frames: Raw ICO buffers on the file.

    """

    _data: bytes
    _offset: int
    header: AniHeader
    sequence: list[int]
    rates: list[int]
    frames: list[bytes]

    def __init__(self, buffer: bytes):
        """
        Create an instance object of this class.

        Args:
            buffer (bytes): ANI data.

        """
        self._data = buffer
        self._offset = 0
        self._validate_signature()
        self.header = self._parse_header()
        self.sequence = self._parse_sequence(self.header.sequence)
        self.rates = self._parse_rates(self.header.sequence)
        self.frames = self._parse_frames()

    @classmethod
    def from_file(cls, path: pathlib.Path) -> AniData:
        """
        Alternate constructor method from a file.

        Args:
            path: ANI file path.

        Returns:
            instance constructed from path.

        """
        with open(path, "rb") as f:
            buffer = f.read()

        return cls(buffer=buffer)

    def unpack(self, format: str) -> tuple[Any, ...]:
        """
        Unpack a set of values according to format.

        Automatically advances the internal offset by format size bytes.

        Args:
            format (str): Unpacking format, according to the specifications of
            the struct module.

        Returns:
            tuple: Unpacked values according to format.

        See Also:
            https://docs.python.org/3/library/struct.html#format-strings

        """
        values = struct.unpack_from(format, self._data, self._offset)
        self._offset += struct.calcsize(format)

        return values

    def findall(self, sub: bytes) -> Iterable[int]:
        """
        Find all instances of the `sub` bytearray on the ani data.

        Args:
            sub (bytes): bytearray to find.

        Yields:
            int: The next index where `sub` is located plus 4.

        Examples:
            >>> self._data = b"...LIST...LIST..."
            >>> [i for i in self.findall(sub=b"LIST")]
            [7,14]

        """
        i = -1
        while (i := self._data.find(sub, i + 5)) != -1:
            yield i + 4

    def _validate_signature(self) -> None:
        riff, size, acon = self.unpack("<4sI4s")

        if riff != b"RIFF":
            raise ValueError("Invalid RIFF file signature")

        if (buffer_size := size + 8) != len(self._data):
            raise ValueError(
                f"Expected buffer size {buffer_size}, got {len(self._data)}"
            )

        if acon != b"ACON":
            raise ValueError("Invalid ANI file signature")

    def _parse_header(self) -> AniHeader:
        anih, chunk_size = self.unpack("<4sI")
        header = AniHeader(*self.unpack("<9I"))

        if header.size != chunk_size:
            raise ValueError("Chunk and header sizes differ")

        return header

    def _parse_sequence(self, af_sequence: bool) -> list[int]:
        """
        Obtain the sequence list for this file.

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

            # Coincidental bytearray
            if self.unpack("<I")[0] / 4 != self.header.steps:
                continue

            seq = [self.unpack("<I")[0] for _ in range(self.header.steps)]

            # Invalid step index
            if any(s > self.header.steps for s in seq):
                continue

            return seq

        return list(range(self.header.steps))

    def _parse_rates(self, af_sequence: bool) -> list[int]:
        """
        Obtain the rate for each frame in the sequence.

        Args:
            af_sequence (bool): if the AF_SEQUENCE bit is on.

        Returns:
            list: Frame sequence rates, in milliseconds.

        """
        count = self.header.steps if af_sequence else self.header.frames

        for offset in self.findall(b"rate"):
            self._offset = offset

            # Coincidental bytearray
            if self.unpack("<I")[0] / 4 != count:
                continue

            return [self.unpack("<I")[0] for _ in range(count)]

        return [self.header.jifrate] * count

    def _parse_frames(self) -> list[bytes]:
        """
        Parse all ico files from the internal data buffer.

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
