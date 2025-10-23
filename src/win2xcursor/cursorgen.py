import logging
import pathlib
import struct
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def parse_ani(ani_file: pathlib.Path) -> tuple[int, int, int, int, bytes]:
    """
    Parses up to the header of an ANI formatted file.

    Args:
        ani_file (pathlib.Path): Path to the ANI file.

    Returns:
        Tuple: Quintuple with relevant values for file conversion.
                - Frames in the file
                - Steps in the animation (a higher value means frames are used
                  more than once)
                - Time per frame (in 1/60s)
                - File flags
                - File buffer starting at the location of the LIST of frames
    Raises:
        ValueError: incorrect file type or a file with the wrong size.
    """
    with open(ani_file, "rb") as f:
        data = f.read()

    offset = struct.calcsize("<4sI")

    # RIFF header
    ftype, size = struct.unpack_from("<4sI", data, 0)
    if ftype != b"RIFF":
        raise ValueError("Not a RIFF file")

    if size + 8 != len(data):
        raise ValueError(f"Expected file size {size + 8}, got {len(data)}")

    # TODO: parse author and title fields if they exist

    rifftype, anih = struct.unpack_from("<4s4s", data, offset)
    offset += struct.calcsize("<4s4s")

    if rifftype != b"ACON" or anih != b"anih":
        raise ValueError("Expected an .ani file")

    # ANIH data
    anihsize = struct.unpack_from("<I", data, offset)[0]
    offset += 4

    _, frames, steps, *_, jifrate, fl = struct.unpack_from("<9I", data, offset)
    offset += anihsize

    return frames, steps, jifrate, fl, data[offset:]


def ico_to_png(data: bytes, offset: int) -> tuple[Image.Image, int, int, int]:
    """
    Transforms an .ico buffer into a PNG image.

    Args:
        data (bytes): buffer containing .ico data
        offset (int): starting position for the .ico

    Returns:
        tuple: PNG image, x/y hotspots, offset at the end of the .ico

    Raises:
        ValueError: data is not in .ico format (no x/y hotspot).
    """
    _, icolength = struct.unpack_from("<4sI", data, offset)
    offset += struct.calcsize("<4sI")

    # Check .ico type -> 2 contains X/Y offsets
    if (struct.unpack_from("<H", data, offset + 2)[0]) != 2:
        x, y = 0, 0
    else:
        x, y = struct.unpack_from("<HH", data, offset + 10)

    with Image.open(BytesIO(data[offset : offset + icolength])) as img:
        img = img.convert("RGBA")
        pixels = np.array(img)

        # HACK: black pixel: usually a bg pixel from RGB images
        threshold = 0
        r, g, b, _ = pixels.T
        black_areas = (r <= threshold) & (g <= threshold) & (b <= threshold)
        pixels[..., 3][black_areas.T] = 0

        img = Image.fromarray(pixels)

    return img, x, y, offset + icolength


def get_frame_sequence(data: bytes, steps: int) -> list[int]:
    """
    Finds the sequence of frames in an .ani file.

    Args:
        data (bytes): ani file buffer.
        steps (int): expected number of frames in the sequence.

    Returns:
        list: Frame sequence.

    """
    seqoffset = data.find(b"seq") + 4

    if seqoffset == -1:
        return list(range(steps))

    seqsteps = struct.unpack_from("<I", data, seqoffset)[0] / 4

    # NOTE: if this matches we're probably not looking at random seq bytes
    #       or... there's only a 2^-32 chance of it anyway 🤓
    if seqsteps != steps:
        return list(range(steps))

    return [
        struct.unpack_from("<I", data, seqoffset + 4 * (i + 1))[0]
        for i in range(steps)
    ]


def cursorfile_from_ani(
    ani_file: pathlib.Path,
    xcursorfiles_dir: pathlib.Path,
    frames_dir: pathlib.Path,
    scale: int,
) -> pathlib.Path:
    """
    Generates a .cursor file from an .ani file.

    Args:
        ani_file (pathlib.Path): Name of the ani file.
        xcursorfiles_dir (pathlib.Path): Path to `xcursorfiles` subdirectory.
        frames_dir (pathlib.Path): Path to `frames` subdirectory.
        scale (int): Cursor resize scale. Recommended for smaller cursors

    Returns:
        pathlib.Path: Path where the .cursor file was written
    """
    frames, steps, jifrate, fl, data = parse_ani(ani_file)
    paths = []
    cursorfile = xcursorfiles_dir.joinpath(f"{ani_file.stem}.cursor")
    seq = get_frame_sequence(data, steps)

    # The last 'LIST' element in an ani file points to icons
    # 'LIST' + size + 'fram'
    offset = data.rfind(b"LIST") + struct.calcsize("<4sI4s")

    logger.debug(f"File metadata for {ani_file!s}")
    logger.debug(f"\t- Frames: {frames}")
    logger.debug(f"\t- Steps: {steps}")
    logger.debug(f"\t- Rate: {jifrate} ({int(1000 * jifrate / 60)} ms)")
    logger.debug(
        f"\t- Flags: AF_ICON {(fl & 0x1) > 0} AF_SEQUENCE {(fl & 0x2) > 0}"
    )
    logger.debug(f"\t- Sequence: {seq}\n")

    # Transform each .ico frame into a PNG
    x, y, size = 0, 0, 0
    for i in range(frames):
        index = str(i + 1).zfill(len(str(frames)))
        img, x, y, offset = ico_to_png(data, offset)
        size = img.width * scale

        if scale > 1:
            img = ImageOps.scale(img, scale, Image.Resampling.NEAREST)

        frame_file = frames_dir.joinpath(f"{ani_file.stem}{index}.png")
        img.save(frame_file)
        paths.append(f"./frames/{ani_file.stem}{index}.png")

    # Create the .cursor file
    with open(cursorfile, "w") as f:
        for i in range(len(seq)):
            f.write(
                f"{size} {x * scale} {y * scale} {paths[seq[i]]} {1000 * jifrate / 60}\n"
            )

    return cursorfile
