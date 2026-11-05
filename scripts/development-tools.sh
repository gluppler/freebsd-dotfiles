#!/bin/sh
# Build development tools as the desktop user with native FreeBSD toolchains.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
export PATH=/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin
export CC=/usr/bin/clang CXX=/usr/bin/clang++ UV_PYTHON_DOWNLOADS=never
export GOTOOLCHAIN=local GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/development.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" efm "$work/efm"
sh "$repo/scripts/stage-licenses.sh" efm "$work/efm" "$repo/.build/prefix"
go=$(sh "$repo/home/.local/bin/nostromo-tool" --path go)
(
    cd "$work/efm"
    export CGO_ENABLED=0
    "$go" mod download
    "$go" mod verify
    "$go" test -mod=readonly ./...
    "$go" build -mod=readonly -trimpath -o "$work/efm-langserver" .
)
install -m 755 "$work/efm-langserver" "$repo/.build/prefix/bin/efm-langserver"
environment=$repo/.build/python-lsp
if [ ! -d "$environment" ]; then
    uv venv --python /usr/local/bin/python3.12 --system-site-packages "$environment"
fi
[ ! -L "$environment" ] && [ -x "$environment/bin/python" ] || exit 1
uv pip install --python "$environment/bin/python" --no-deps --only-binary :all: \
    --require-hashes -r "$repo/scripts/python-lsp.requirements"
uv pip check --python "$environment/bin/python"
"$environment/bin/python" -c 'import pylsp, pylsp_ruff, cattrs, lsprotocol; from importlib.metadata import version; assert version("python-lsp-ruff") == "2.3.4"'
environment=$repo/.build/embedded-python
if [ ! -d "$environment" ]; then
    uv venv --python /usr/local/bin/python3.12 --system-site-packages "$environment"
fi
[ ! -L "$environment" ] && [ -x "$environment/bin/python" ] || exit 1
uv pip install --python "$environment/bin/python" --no-deps --only-binary :all: \
    --require-hashes -r "$repo/scripts/embedded.requirements"
uv pip check --python "$environment/bin/python"
"$environment/bin/west" --version
"$environment/bin/python" -c 'import yaml, jsonschema, pykwalify, elftools, serial, intelhex, esptool'
mkdir -p "$repo/.build/prefix/share/man/man1"
install -m 644 "$repo/docs/man/nostromo-docs.1" "$repo/.build/prefix/share/man/man1/"
# FreeBSD renames the editor and its manual to vise; our command is vis.
test -r /usr/local/share/man/man1/vise.1.gz
ln -sf /usr/local/share/man/man1/vise.1.gz "$repo/.build/prefix/share/man/man1/vis.1.gz"
makewhatis "$repo/.build/prefix/share/man"
reference=$repo/.build/docs/cppreference-20250209
if [ ! -e "$reference" ]; then
    sh "$repo/scripts/fetch-source.sh" cppreference "$reference"
fi
[ ! -L "$reference" ] && [ -s "$reference/en/c.html" ] && [ -s "$reference/en/cpp.html" ]
