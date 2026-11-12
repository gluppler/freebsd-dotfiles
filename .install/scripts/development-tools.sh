#!/bin/sh
# Build development tools as the desktop user with native FreeBSD toolchains.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
export PATH=/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin
export CC=/usr/bin/clang CXX=/usr/bin/clang++ UV_PYTHON_DOWNLOADS=never
export GOTOOLCHAIN=local GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org
# Like CARGO_HOME, tool caches belong to the build output that a clean install
# removes, not to the home.
export GOPATH="$repo/.build/go" GOCACHE="$repo/.build/go-cache" GOFLAGS=-modcacherw UV_CACHE_DIR="$repo/.build/uv-cache"
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/development.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" efm "$work/efm"
sh "$repo/.install/scripts/stage-licenses.sh" efm "$work/efm" "$repo/.build/prefix"
go=$(sh "$repo/bin/nostromo-tool" --path go)
(
    cd "$work/efm"
    # Go's local usage counters would otherwise start in ~/.config/go.
    export CGO_ENABLED=0 XDG_CONFIG_HOME="$work/config"
    "$go" mod download
    "$go" mod verify
    "$go" test -mod=readonly ./...
    "$go" build -mod=readonly -trimpath -o "$work/efm-langserver" .
)
install -m 755 "$work/efm-langserver" "$repo/.build/prefix/bin/efm-langserver"
# uv pip check reads only an environment's own site-packages, not the reviewed
# system packages these wheels import. Check the wheels against both.
check_requirements() {
    "$1/bin/python" -I - <<'EOF'
import sys
import sysconfig
from importlib.metadata import PackageNotFoundError, distributions, version
from packaging.requirements import Requirement

failed = False
for dist in distributions(path=[sysconfig.get_path('purelib')]):
    for line in dist.requires or ():
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate({'extra': ''}):
            continue
        try:
            found = version(requirement.name)
        except PackageNotFoundError:
            found = None
        if found is None or not requirement.specifier.contains(found, prereleases=True):
            print(f"{dist.metadata['Name']} requires {requirement}; found {found or 'none'}.", file=sys.stderr)
            failed = True
sys.exit(failed)
EOF
}
environment=$repo/.build/python-lsp
if [ ! -d "$environment" ]; then
    uv venv --python /usr/local/bin/python3.12 --system-site-packages "$environment"
fi
[ ! -L "$environment" ] && [ -x "$environment/bin/python" ] || exit 1
uv pip install --python "$environment/bin/python" --no-deps --only-binary :all: \
    --require-hashes -r "$repo/.install/scripts/python-lsp.requirements"
check_requirements "$environment"
"$environment/bin/python" -c 'import pylsp, pylsp_ruff, cattrs, lsprotocol; from importlib.metadata import version; assert version("python-lsp-ruff") == "2.3.4"'
environment=$repo/.build/embedded-python
if [ ! -d "$environment" ]; then
    uv venv --python /usr/local/bin/python3.12 --system-site-packages "$environment"
fi
[ ! -L "$environment" ] && [ -x "$environment/bin/python" ] || exit 1
uv pip install --python "$environment/bin/python" --no-deps --only-binary :all: \
    --require-hashes -r "$repo/.install/scripts/embedded.requirements"
check_requirements "$environment"
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
    sh "$repo/.install/scripts/fetch-source.sh" cppreference "$reference"
fi
[ ! -L "$reference" ] && [ -s "$reference/en/c.html" ] && [ -s "$reference/en/cpp.html" ] || {
    echo 'The cppreference archive did not provide the C and C++ references.' >&2
    exit 1
}
# The extracted reference replaces its archive.
rm -f "$repo/.build/downloads/cppreference.tar.gz"
sh "$repo/.install/scripts/docs-library.sh"
