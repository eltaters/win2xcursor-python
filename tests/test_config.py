import logging
import pathlib
import unittest

import msgspec.toml

from win2xcursor import Config, Cursor

logging.disable()


class TestConfig(unittest.TestCase):
    def test_empty(self) -> None:
        buffer = rb"""
        """
        config = msgspec.toml.decode(buffer, type=Config)
        self.assertEqual(config.scale, 1)
        self.assertEqual(config.cursors, [])

    def test_invalid_scale(self) -> None:
        buffer = rb"""
        scale = 0
        """
        with self.assertRaises(msgspec.ValidationError):
            msgspec.toml.decode(buffer, type=Config)

    def test_missing_double_brackets(self) -> None:
        buffer = rb"""
        [cursor]
        name = "default"
        file = "default.ani"
        aliases = []
        """
        with self.assertRaises(msgspec.ValidationError):
            msgspec.toml.decode(buffer, type=Config)

    def test_multiple_cursors(self) -> None:
        buffer = rb"""
        [[cursor]]
        name = "default"
        file = "default.ani"
        aliases = []

        [[cursor]]
        name = "help"
        file = "help.ani"
        aliases = []
        """
        config = msgspec.toml.decode(buffer, type=Config)
        self.assertEqual(len(config.cursors), 2)

    def test_empty_cursor(self) -> None:
        buffer = rb"""
        """
        with self.assertRaises(msgspec.ValidationError):
            msgspec.toml.decode(buffer, type=Cursor)

    def test_missing_name(self) -> None:
        buffer = rb"""
        file = "default.ani"
        aliases = []
        """
        with self.assertRaises(msgspec.ValidationError):
            msgspec.toml.decode(buffer, type=Cursor)

    def test_missing_file(self) -> None:
        buffer = rb"""
        name = "default"
        aliases = []
        """
        with self.assertRaises(msgspec.ValidationError):
            msgspec.toml.decode(buffer, type=Cursor)

    def test_missing_aliases(self) -> None:
        buffer = rb"""
        name = "default"
        file = "default.ani"
        """
        config = msgspec.toml.decode(buffer, type=Cursor)
        self.assertEqual(config.aliases, [])

    def test_cursor_file_no_abspath(self) -> None:
        buffer = rb"""
        [[cursor]]
        name = "default"
        file = "default.ani"
        aliases = []
        """
        config = msgspec.toml.decode(buffer, type=Config)
        path = pathlib.Path(config.cursors[0].file)
        self.assertEqual(len(pathlib.Path("./ani/default.ani").parts), 2)
        self.assertEqual(len(path.parts), 1)
