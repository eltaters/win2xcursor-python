"""Defines the CLI for converting Windows animated cursors to Linux."""

import logging
import os
import pathlib
import subprocess
import sys

import msgspec.toml

from win2xcursor.ani import AniData
from win2xcursor.args import setup_parser
from win2xcursor.config import Config
from win2xcursor.cursor import CursorFile
from win2xcursor.frames import FrameScaler
from win2xcursor.theme import ThemeDirectory

logger = logging.getLogger(__package__)


def main() -> int:
    """
    Entry point to the program.

    Returns:
        Exit code -- zero indicates success; non-zero indicates failure.

    """
    # Parse command-line arguments
    parser = setup_parser()
    args = parser.parse_args()

    # Initialize logging
    level = logging.INFO if not args.debug else logging.DEBUG
    _logging_subscriber(level)

    # Prepare theme directory
    theme = ThemeDirectory(args.theme_dir)
    theme.setup()
    theme.create_index_theme()

    # Main script
    print("=" * 80, file=sys.stderr)
    print("WIN2XCUR PYTHON SCRIPT".center(80, " "), file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    with open(theme.config_toml, "rb") as f:
        buffer = f.read()

    try:
        config = msgspec.toml.decode(buffer, type=Config)
    except msgspec.ValidationError as err:
        # TODO: Remove when `err` prints a custom error message -
        # https://github.com/eltaters/win2xcursor/pull/9#issuecomment-3453381998
        logger.error("Invalid config: %s", err)
        return os.EX_DATAERR

    for cursor in config.cursors:
        ani_file = theme.ani.joinpath(cursor.file)

        if not ani_file.exists():
            logger.warning(
                "%s: file not found: %s; skipping",
                cursor.name,
                cursor.file,
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

        # Create the `.cursor` configuration file.
        xconfig_file = theme.xcursorfiles.joinpath(ani_file.stem)
        xconfig = CursorFile(data, theme.frames)
        xconfig.add(frames.get_frames(config.scale))
        xconfig.save(xconfig_file)

        # Create the Xcursor.
        cursor_file = theme.cursors.joinpath(cursor.name)
        try:
            _create_cursor(xconfig_file, cursor_file, theme.path)
        except subprocess.CalledProcessError:
            continue

        for alias in cursor.aliases:
            _create_alias(alias, cursor_file, theme.path, theme.cursors)

        print("", file=sys.stderr)
        print("-" * 80, file=sys.stderr, end="\n\n")

    if not args.debug:
        theme.cleanup()

    logger.info("Finished creating cursors! 🚀🚀")
    return os.EX_OK


def _logging_subscriber(level: int) -> None:
    """Initialize the logger to begin outputting events."""
    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(fmt="%(levelname)s %(message)s", style="%")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)


def _create_cursor(
    config: pathlib.Path,
    output: pathlib.Path,
    theme_dir: pathlib.Path,
) -> None:
    """Convert PNG files into an animated Xcursor."""
    try:
        _ = subprocess.run(
            ["xcursorgen", config, output],
            check=True,
            cwd=theme_dir,
        )
    except subprocess.CalledProcessError as err:
        logger.error(f"failed to create Xcursor: {err}")
        raise err
    else:
        logger.info(f"created cursor: {output.name}")


def _create_alias(
    alias: str,
    xcursor_file: pathlib.Path,
    theme_dir: pathlib.Path,
    cursors_dir: pathlib.Path,
) -> None:
    """
    Create an alias for a cursor file.

    Args:
        alias: Name for symbolic link.
        xcursor_file: Original cursor path.
        theme_dir: Cursor theme directory.
        cursors_dir: Cursor files directory.

    """
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
