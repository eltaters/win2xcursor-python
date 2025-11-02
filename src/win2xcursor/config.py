from typing import Annotated

from msgspec import Meta, Struct, field


class Cursor(Struct, kw_only=True):
    """Represents an ANI file to convert.

    Attributes:
        name (str): Unique name for the cursor.
        file (str): Name of the ANI file from the `<theme>/ani` subdirectory.
        aliases (list): Alternative names to link `name` to for compatibility
                        with different applications.
    """

    name: str
    file: str
    aliases: list[str] = []


class Config(Struct, kw_only=True):
    """Represents the main configuration of the cursor theme.

    Attributes:
        scale (int): Factor to enlarge the cursor by.
        cursors (list): Array of cursor definitions.
    """

    scale: Annotated[int, Meta(ge=1)] = 1
    cursors: list[Cursor] = field(default=[], name="cursor")
