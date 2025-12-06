"""Groups theme-related functionality together."""

import logging
import pathlib
import shutil

logger = logging.getLogger(__name__)


class ThemeDirectory:
    """Represents the theme directory for which we are generating cursors."""

    def __init__(self, base: pathlib.Path) -> None:
        """Create an instance of `ThemeDirectory`."""
        self._base = base

    @property
    def path(self) -> pathlib.Path:
        """Path to the root of the theme directory."""
        return self._base

    @property
    def ani(self) -> pathlib.Path:
        """Path to the directory containing all of the ANI files."""
        return self._base.joinpath("ani")

    @property
    def frames(self) -> pathlib.Path:
        """Path to the directory containing the extracted PNG frames."""
        return self._base.joinpath("frames")

    @property
    def xcursorfiles(self) -> pathlib.Path:
        """Path to the directory containing the generated `.cursor` files."""
        return self._base.joinpath("xcursorfiles")

    @property
    def cursors(self) -> pathlib.Path:
        """Path to the directory containing the generated cursors."""
        return self._base.joinpath("cursors")

    @property
    def index_theme(self) -> pathlib.Path:
        """Path to the `index.theme` file at the root of the theme."""
        return self._base.joinpath("index.theme")

    @property
    def config_toml(self) -> pathlib.Path:
        """Path to the cursor configuration file at the root of the theme."""
        return self._base.joinpath("config.toml")

    def setup(self) -> None:
        """Create all the directories necessary for this project."""
        directories = (
            self.frames,
            self.xcursorfiles,
            self.cursors,
        )

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info("Created directory: %r", directory)

    def cleanup(self) -> None:
        """Remove all of the intermediate build files."""
        directories = (
            self.xcursorfiles,
            self.frames,
        )

        for directory in directories:
            shutil.rmtree(directory)
            logger.info("Deleted directory: %r", directory)

    def create_index_theme(self) -> None:
        """Generate the `index.theme` file."""
        text = (
            "[Icon Theme]\n"
            + f"Name={self.path.name}\n"
            + "Inherits=breeze_cursors"
        )

        try:
            self.index_theme.write_text(text)
        except OSError as err:
            logger.error("Failed to create index.theme: %s", err)
        else:
            logger.info("Created file: %r", self.index_theme.name)
