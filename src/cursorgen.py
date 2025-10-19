import struct
from io import BytesIO
from PIL import Image
import numpy as np


def parse_ani(anifile, path):
    with open(f"{path}/ani/{anifile}", "rb") as f:
        data = f.read()

    offset = struct.calcsize("<4sI")

    # RIFF header
    ftype, size = struct.unpack_from("<4sI", data, 0)
    if ftype != b"RIFF":
        raise ValueError("Not a RIFF file")

    if size + 8 != len(data):
        raise ValueError(f"Expected file size {size + 8}, got {len(data)}")

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


def ico_to_png(data, offset):
    _, icolength = struct.unpack_from("<4sI", data, offset)
    offset += struct.calcsize("<4sI")

    # Check .ico type -> 2 contains X/Y offsets
    if (struct.unpack_from("<H", data, offset + 2)[0]) != 2:
        raise ValueError("Frame is not a cursor")

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


def get_frame_sequence(data, steps):
    seqoffset = data.find(b"seq") + 4
    seqsteps = struct.unpack_from("<I", data, seqoffset)[0] / 4

    # NOTE: if this matches we're probably not looking at random seq bytes
    #       or... there's only a 2^-32 chance of it anyway 🤓
    if seqsteps != steps:
        return list(range(steps))

    return [
        struct.unpack_from("<I", data, seqoffset + 4 * (i + 1))[0] for i in range(steps)
    ]


def cursorfile_from_ani(anifile: str, path: str):
    frames, steps, jifrate, fl, data = parse_ani(anifile, path)
    paths = []
    cpath = f"{path}/xcursorfiles/{anifile[:-4]}.cursor"
    seq = get_frame_sequence(data, steps) if fl & 0x2 else list(range(steps))

    # The last 'LIST' element in an ani file points to icons
    offset = data.rfind(b"LIST") + struct.calcsize("<4sI4s")  # 'LIST' + size + 'fram'

    print(f"File metadata for {path}/ani/{anifile}")
    print(f"\t- Frames: {frames}")
    print(f"\t- Steps: {steps}")
    print(f"\t- Rate: {jifrate} ({int(1000 * jifrate / 60)} ms)")
    print(f"\t- Flags: AF_ICON {(fl & 0x1) > 0} AF_SEQUENCE {(fl & 0x2) > 0}")
    print(f"\t- Sequence: {seq}\n")

    # Transform each .ico frame into a PNG
    x, y, size = 0, 0, 0
    for i in range(frames):
        index = str(i + 1).zfill(len(str(frames)))
        img, x, y, offset = ico_to_png(data, offset)
        size = img.width

        img.save(f"{path}/frames/{anifile[:-4]}{index}.png")
        paths.append(f"./frames/{anifile[:-4]}{index}.png")

    # Create the .cursor file
    with open(cpath, "w") as f:
        for i in range(len(seq)):
            f.write(f"{size} {x} {y} {paths[seq[i]]} {1000 * jifrate / 60}\n")

    return cpath
