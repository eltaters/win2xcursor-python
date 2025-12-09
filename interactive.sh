#!/usr/bin/env bash

red() {
    local -r message="$1"
    echo -e "\e[31m$message\e[39m"
}

green() {
    local -r message="$1"
    echo -e "\e[32m$message\e[39m"
}

yellow() {
    local -r message="$1"
    echo -e "\e[33m$message\e[39m"
}

cyan() {
    local -r message="$1"
    echo -e "\e[36m$message\e[39m"
}

set -e
[ ! -z "${TRACE+x}" ] && set -x

echo "██╗    ██╗██╗███╗   ██╗██████╗ ██╗  ██╗ ██████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ "
echo "██║    ██║██║████╗  ██║╚════██╗╚██╗██╔╝██╔════╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗"
echo "██║ █╗ ██║██║██╔██╗ ██║ █████╔╝ ╚███╔╝ ██║     ██║   ██║██████╔╝███████╗██║   ██║██████╔╝"
echo "██║███╗██║██║██║╚██╗██║██╔═══╝  ██╔██╗ ██║     ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗"
echo "╚███╔███╔╝██║██║ ╚████║███████╗██╔╝ ██╗╚██████╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║"
echo " ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝"
echo "                               INTERACTIVE INSTALLER                                     "
echo ""

if ! command -v xcursorgen > /dev/null; then
    red "error: expected xcursorgen to be installed" >&2
    exit 1
fi
green "+ xcursorgen is installed"

if ! command -v win2xcursor > /dev/null; then
    repository="git+https://github.com/eltaters/win2xcursor"

    if command -v uv; then
        uv pip install "$repository"
    elif command -v pip; then
        pip install "$repository"
    elif command -v python3; then
        python -m pip install "$repository"
    else
        red "error: expected win2xcursor to be installed" >&2
        exit 1
    fi
fi
green "+ win2xcursor is installed"

echo ""
# TODO: Figure out how to enable autocomplete for this prompt.
read -p "Path to directory containing ANI files: " path_to_cursors
eval path_to_cursors="$path_to_cursors"

if ! test -d $path_to_cursors; then
    red "error: expected path to an existing directory" >&2
    exit 1
fi

file_count="$(find "$path_to_cursors" -type f -name '*.ani' -printf '.' | wc -c)"
yellow "Found $file_count ANI file(s)"

# TODO: Loop until a valid theme_name has been set.
read -p "Theme name to create: " theme_name

theme_dir="${XDG_DATA_HOME:-${HOME:-/}/.local/share/icons}/$theme_name"

if test -d "$theme_dir"; then
    red "error: theme with the same name already exists" >&2
    exit 1
fi

mkdir --parents "$theme_dir/ani"
cp "$path_to_cursors"/*.ani "$theme_dir/ani"
curl -SsLo "$theme_dir/config.toml" -- "https://raw.githubusercontent.com/eltaters/win2xcursor/refs/heads/main/config.toml"

echo ""
green "Theme directory has been set up!"
echo ""
echo "Next steps:"
echo "- Go to theme directory:"
cyan "  cd $theme_dir"
echo "- Update configuration file:"
cyan "  \$EDITOR ./config.toml"
echo "- Run the script:"
cyan "  win2xcursor"
