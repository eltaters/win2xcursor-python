import argparse
import logging
import pathlib
import subprocess
import sys

import msgspec.toml

from . import __version__
from .config import Config
from .cursorgen import cursorfile_from_ani

logger = logging.getLogger(__package__)


def main() -> int:
    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(fmt="{levelname} {message}", style="{")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Argument parsing
    parser = argparse.ArgumentParser(
        prog="win2xcursor",
        description="Python script to transform .ani files into xcursors",
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
        "-V",
        "--version",
        action="version",
        version=f"{__package__} {__version__}",
    )
    args = parser.parse_args()

    # ======================================================================= #
    # You can delete the xcursorfiles and frames directories after running    #
    # the script, I'll leave them there so the process is understood a bit    #
    # better and to manually handle part of the process if the script fails   #
    # ======================================================================= #

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
            continue

        cursorfile = cursorfile_from_ani(
            ani_file,
            xcursorfiles_dir,
            frames_dir,
            config.scale,
        )

        xcursor_file = cursors_dir.joinpath(cursor.name)

        # create the cursor with xcursorgen
        logger.info(f"Creating cursor: {xcursor_file.name}")
        try:
            _ = subprocess.run(
                [
                    "xcursorgen",
                    cursorfile,
                    xcursor_file,
                ],
                check=True,
                cwd=theme_dir,
            )
        except subprocess.CalledProcessError as err:
            logger.error(f"failed to create Xcursor: {err}")
            return 1

        # create all defined aliases
        for alias in cursor.aliases:
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

        print("", file=sys.stderr)
        print("-" * 80, file=sys.stderr, end="\n\n")

    # finally, create the index.theme
    index_theme = theme_dir.joinpath("index.theme")
    index_theme.write_text(
        "[Icon Theme]\n"
        + f"Name={theme_dir.name}\n"
        + "Inherits=breeze_cursors"
    )
    logger.info(f"created file: {index_theme.name}")

    logger.info("Finished creating cursors! 🚀🚀")
    return 0


if __name__ == "__main__":
    sys.exit(main())
