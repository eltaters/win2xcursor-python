# win2xcursor

A python script to parse windows .ani cursors via xcursorgen.  
Inspired from the desire to bring NOiiRE's [beautiful cursors](https://ko-fi.com/noiire/shop) to linux.

## Installation

This script requires the `numpy` and `pillow` libaries, which you can set up through a python virtual environment:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install .
```

You will also need to install xcursorgen for the script to generate the cursors:

```bash
# Arch
sudo pacman -S xcursorgen

# Debian/Mint/Ubuntu
sudo apt install xcursorgen

# Fedora
sudo dnf install xcursorgen
```

## Usage

Before using the script, you need to do the following:

1. Create a new directory for your theme:
  ```bash
  # To install the theme for the current user:
  $ cd ~/.local/share/icons

  # To install the theme for everyone on the system:
  # $ cd /usr/share/icons

  $ mkdir -p <ThemeName>/ani
  ```
2. Copy your .ani files to `~/.local/share/icons/<ThemeName>/ani`
3. Create a `config.toml` file in `~/.local/share/icons/<ThemeName>`

After this setup, you can proceed to run the script:

```bash
$ win2xcursor --theme=<ThemeName>
```

### config.toml

The config file for this project consists of a series of cursor items, each of which with the next structure:

```toml
[[cursor]]
file = "..." # The name of your ANI file, ending on .ani
name = "..." # The name of the associated cursor
aliases =  ["..."] # Cursor aliases
```

The `aliases` property should be defined as an empty list `[]` when a cursor has no defined aliases.
Additionally, smaller cursors can also be **scaled** by specifying a `scale=<number>`, property.

A template `config.toml` file has been provided in this repository, which contains most of the standard cursor names/aliases and a few additional associations for normally lacking icons.

## Video Showcase

https://github.com/user-attachments/assets/22868d14-59f3-4dbf-b613-9d48d116f936
