from typing import Annotated

from msgspec import Meta, Struct, field


class Cursor(Struct, kw_only=True):
    """Represents an ANI file to convert.

    Attributes
    ----------
    name
        A unique name for the cursor (typically a standard X11 cursor name).
    file
        The name of the ANI file from the `<theme>/ani` subdirectory.
    aliases
        Alternative names to link `name` to for compatibility with different
        applications (e.g., `normal` -> `default` or `left_ptr`).
    """

    name: str
    file: str
    aliases: list[str] = []


class Config(Struct, kw_only=True):
    """Represents the main configuration of the cursor theme.

    Attributes
    ----------
    scale
        An optional factor to enlarge the cursor by. Defaults to `1`.
    cursors
        Array of cursor definitions.
    """

    scale: Annotated[int, Meta(ge=1)] = 1
    cursors: list[Cursor] = field(default=[], name="cursor")
