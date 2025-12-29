"""Defines the configurable options exposed via the command-line interface."""

import argparse
import pathlib

from win2xcursor import __version__


def setup_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for this application.

    Returns:
        Fully configured argument parser.

    """
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
