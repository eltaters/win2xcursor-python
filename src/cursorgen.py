import struct
from io import BytesIO
from PIL import Image, ImageOps
import numpy as np
from typing import Tuple
import logging


def parse_ani(anifile: str, path: str) -> Tuple[int, int, int, int, bytes]:
    """
    Parses initial contents of a RIFF formatted .ani file.

    Args:
        anifile: Name of the file
        path: Base path for the cursor theme

    Returns:
        Tuple: Quintuple with relevant values for file conversion.
                - Frames in the file
                - Steps in the animation (a higher value means frames are used
                  more than once)
                - Time per frame (in 1/60s)
                - File flags
                - File buffer starting at the location of the LIST of frames
    Raises:
        ValueError: on an incorrect file type or a file with the wrong size.
    """
    with open(f"{path}/ani/{anifile}", "rb") as f:
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


def ico_to_png(data: bytes, offset: int) -> Tuple:
    """
    Transforms an .ico buffer into a PNG image.

    Args:
        data (bytes): buffer containing .ico data
        offset (int): starting position for the .ico

    Returns:
        Tuple: PNG image, x/y hotspots, offset at the end of the .ico

    Raises:
        ValueError: if the .ico is not a cursor, which meansit does not have a
                    x/y hotspot.
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


def get_frame_sequence(data: bytes, steps: int) -> list:
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
        struct.unpack_from("<I", data, seqoffset + 4 * (i + 1))[0] for i in range(steps)
    ]


def cursorfile_from_ani(anifile: str, path: str, scale: int):
    """
    Generates a .cursor file from an .ani file.

    Args:
        anifile (str): Name of the ani file.
        path (str): Base theme path.
        scale (int): Cursor resize scale. Recommended for smaller cursors

    Returns:
        str: Path where the .cursor file was written
    """
    frames, steps, jifrate, fl, data = parse_ani(anifile, path)
    paths = []
    cpath = f"{path}/xcursorfiles/{anifile[:-4]}.cursor"
    seq = get_frame_sequence(data, steps)

    # The last 'LIST' element in an ani file points to icons
    offset = data.rfind(b"LIST") + struct.calcsize("<4sI4s")  # 'LIST' + size + 'fram'

    logging.debug(f"File metadata for {path}/ani/{anifile}")
    logging.debug(f"\t- Frames: {frames}")
    logging.debug(f"\t- Steps: {steps}")
    logging.debug(f"\t- Rate: {jifrate} ({int(1000 * jifrate / 60)} ms)")
    logging.debug(f"\t- Flags: AF_ICON {(fl & 0x1) > 0} AF_SEQUENCE {(fl & 0x2) > 0}")
    logging.debug(f"\t- Sequence: {seq}\n")

    # Transform each .ico frame into a PNG
    x, y, size = 0, 0, 0
    for i in range(frames):
        index = str(i + 1).zfill(len(str(frames)))
        img, x, y, offset = ico_to_png(data, offset)
        size = img.width * scale

        if scale > 1:
            img = ImageOps.scale(img, scale, Image.Resampling.NEAREST)

        img.save(f"{path}/frames/{anifile[:-4]}{index}.png")
        paths.append(f"./frames/{anifile[:-4]}{index}.png")

    # Create the .cursor file
    with open(cpath, "w") as f:
        for i in range(len(seq)):
            f.write(
                f"{size} {x * scale} {y * scale} {paths[seq[i]]} {1000 * jifrate / 60}\n"
            )

    return cpath
