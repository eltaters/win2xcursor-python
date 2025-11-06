import argparse
import logging
import pathlib
import shutil
import subprocess
import sys

import msgspec.toml

from win2xcursor import __version__
from win2xcursor.ani import AniData
from win2xcursor.config import Config
from win2xcursor.cursor import CursorFile
from win2xcursor.frames import FrameScaler

logger = logging.getLogger(__package__)


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="win2xcursor",
        description="Python script to transform .ani files into Xcursors",
        epilog=(
            "This script expects [theme-dir] to be an existing directory with "
            "a config.toml, and your ANI files to be stored in [theme-dir]/ani"
        ),
    )
    parser.add_argument(
        "--theme-dir",
        default=pathlib.Path.cwd(),
        type=pathlib.Path,
        help="Path to the custom theme directory",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use debug output and save intermediate build files",
    )
    parser.add_argument(
        "--ignore-hotspots",
        action="store_true",
        help="Ignore x/y hotspots for the cursor",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{__package__} {__version__}",
    )
    return parser


def main() -> int:
    parser = setup_parser()
    args = parser.parse_args()

    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(fmt="{levelname} {message}", style="{")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)

    # Path to the custom cursor theme.
    theme_dir: pathlib.Path = args.theme_dir

    # Contains all of the ANI files.
    ani_dir = theme_dir.joinpath("ani")

    # PNGs extracted from the ANI files.
    frames_dir = theme_dir.joinpath("frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Generated `.cursor` files.
    xcursorfiles_dir = theme_dir.joinpath("xcursorfiles")
    xcursorfiles_dir.mkdir(parents=True, exist_ok=True)

    # Generated Xcursors
    cursors_dir = theme_dir.joinpath("cursors")
    cursors_dir.mkdir(parents=True, exist_ok=True)

    # Main script

    print("=" * 80, file=sys.stderr)
    print("WIN2XCUR PYTHON SCRIPT".center(80, " "), file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    # Read and parse config file
    config_file = theme_dir.joinpath("config.toml")

    with open(config_file, "rb") as f:
        buffer = f.read()

    try:
        config = msgspec.toml.decode(buffer, type=Config)
    except msgspec.ValidationError as err:
        # TODO(Nic): Nicer error message.
        logger.error(f"invalid config: {err}")
        return 1

    # Process the cursors.
    for cursor in config.cursors:
        ani_file = ani_dir.joinpath(cursor.file)

        # Skip cursors that don't exist.
        if not ani_file.exists():
            logger.warning(
                f"{cursor.name}: file not found: {cursor.file}; skipping"
            )
            print("", file=sys.stderr)
            print("-" * 80, file=sys.stderr, end="\n\n")
            continue

        data = AniData.from_file(ani_file)
        frames = FrameScaler(
            data.frames,
            name=ani_file.stem,
            ignore_hotspots=args.ignore_hotspots,
        )

        # Define and save the `.cursor` file.
        xconfig = CursorFile(data, frames_dir)
        xconfig.add(frames.get_frames(config.scale))
        xconfig_file = xcursorfiles_dir.joinpath(ani_file.stem)
        xconfig.save(xconfig_file)

        # Create the cursor with `xcursorgen`.
        cursor_file = cursors_dir.joinpath(cursor.name)
        try:
            _ = subprocess.run(
                [
                    "xcursorgen",
                    xconfig_file,
                    cursor_file,
                ],
                check=True,
                cwd=theme_dir,
            )
        except subprocess.CalledProcessError as err:
            logger.error(f"failed to create Xcursor: {err}")
            continue
        else:
            logger.info(f"created cursor: {cursor_file.name}")

        for alias in cursor.aliases:
            create_alias(alias, cursor_file, theme_dir, cursors_dir)

        print("", file=sys.stderr)
        print("-" * 80, file=sys.stderr, end="\n\n")

    create_index_theme(theme_dir)

    if not args.debug:
        shutil.rmtree(xcursorfiles_dir)
        logger.info(f"deleted directory: {xcursorfiles_dir}")
        shutil.rmtree(frames_dir)
        logger.info(f"deleted directory: {frames_dir}")

    logger.info("Finished creating cursors! 🚀🚀")
    return 0


def create_alias(
    alias: str,
    xcursor_file: pathlib.Path,
    theme_dir: pathlib.Path,
    cursors_dir: pathlib.Path,
) -> None:
    alias_file = cursors_dir.joinpath(alias)
    alias_file.unlink(missing_ok=True)

    try:
        _ = subprocess.run(
            [
                "ln",
                "--symbolic",
                xcursor_file,
                alias_file,
            ],
            cwd=theme_dir,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        logger.debug(f"command failed: {err.cmd}")
        reason = err.stderr.strip().rsplit(": ", maxsplit=1)[-1]
        logger.error(f"failed to create alias: {alias}: {reason}")
    else:
        logger.info(f"created alias: {alias}")


def create_index_theme(theme_dir: pathlib.Path) -> None:
    index_theme = theme_dir.joinpath("index.theme")
    text = (
        "[Icon Theme]\n"
        + f"Name={theme_dir.name}\n"
        + "Inherits=breeze_cursors"
    )

    try:
        index_theme.write_text(text)
    except OSError as err:
        logger.error(f"failed to create index.theme: {err}")
    else:
        logger.info(f"created file: {index_theme.name}")


if __name__ == "__main__":
    sys.exit(main())
