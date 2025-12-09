# win2xcursor

A python script to parse windows .ani cursors via xcursorgen. Inspired from the
desire to bring [NOiiRE's beautiful cursors] to Linux.

https://github.com/user-attachments/assets/22868d14-59f3-4dbf-b613-9d48d116f936

## Installation

This project is built on top of xcursorgen. Install it using your
distribution's package manager:

```bash
# Arch
sudo pacman -S xcursorgen

# Debian/Mint/Ubuntu
sudo apt install xcursorgen

# Fedora
sudo dnf install xcursorgen
```

Install **win2xcursor** from GitHub using `uv` or `pip`:

```bash
# Using uv:
uv pip install git+https://github.com/eltaters/win2xcursor

# Using pip:
pip install git+https://github.com/eltaters/win2xcursor
```

## Usage

Create a new directory for your theme (`<ThemeName>`):

```bash
# To install the theme for only the current user:
mkdir --parents "$HOME"/.local/share/icons/<ThemeName>/ani

# To install the theme for everyone on the system:
sudo mkdir --parents /usr/share/icons/<ThemeName>/ani
```

Copy your ANI files into `<ThemeName>/ani`:

```bash
cp /path/to/cursors/*.ani "$HOME"/.local/share/icons/<ThemeName>/ani/
```

Use curl to copy the template `config.toml`, or continue reading to learn how
to write it manually:

```bash
curl -SsLo "$HOME"/.local/share/icons/<ThemeName>/config.toml -- https://raw.githubusercontent.com/eltaters/win2xcursor/refs/heads/main/config.toml
```

Finally, run the script:

> [!TIP]\
> If you are inside of `<ThemeDir>`, you can omit the `--theme-dir` flag, as it
> defaults to the current working directory.

```bash
win2xcursor --theme-dir="$HOME"/.local/share/icons/<ThemeName>
```

### Configuration file

The configuration file consists of multiple cursor entries, each with the
following structure:

> [!NOTE]\
> A template `config.toml` file is provided in this repository, which contains
> most of the standard cursor names and aliases, plus a few additional aliases
> for normally lacking icons.

```toml
[[cursor]]
# Name of the ANI file
file = "..."
# Linux-equivalent cursor name
name = "..."
# Additional names (for compatibility with various programs)
aliases = ["..."]
```

The `aliases` property should be defined as an empty list (`[]`) when a cursor
has no defined aliases. Additionally, smaller cursors can also be **scaled** by
specifying a `scale=<number>`, property.

```toml
scale = 1  # A top-level property, not under any individual cursor entry.
```

## Contributions

Contributions are always welcome! Before starting any work, please read the
following guidelines:

### Start with an Issue

1. Open a new issue describing the bug or feature request.
1. If you want to contribute a fix, leave a comment on the issue.
1. Feel free to ask questions!

### Development

- `uv`: Environment/dependency management
- `ruff`: Formatter/linter
- `pre-commit`: Automatic formatting/linting checks

To set up your environment:

```bash
uv venv
source .venv/bin/activate
uv sync
pre-commit install
```

### Code Style

Contributions should pass the following checks:

- Static type analysis: `mypy --strict ./src`
- Documentation: Use **Google-style docstrings**
- Unit tests: `pytest` (update unit tests as needed)

### Branches

The `main` branch should always be **stable**. Create feature branches for your
work (e.g., `feature/add-skip-broken-flag`, `bugfix/42-improper-scaling`,
`docs/update-readme`, etc.)

## License

See [LICENSE](./LICENSE).

[noiire's beautiful cursors]: https://ko-fi.com/noiire/shop
