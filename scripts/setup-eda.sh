#!/bin/sh
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
plugin=$repo/.build/eda/ibom-d1eb5b79a52a2ddc1ce270b63920346463c19b05
if [ ! -e "$plugin" ]; then sh "$repo/scripts/fetch-source.sh" ibom "$plugin"; fi
[ ! -L "$plugin" ] && [ -s "$plugin/InteractiveHtmlBom/generate_interactive_bom.py" ]
sh "$repo/scripts/stage-licenses.sh" ibom "$plugin" "$repo/.build/prefix"
# The packaged tables reference KiCad's versioned library variables. Keep any
# existing user tables, including projects' private library entries.
config=${KICAD_CONFIG_HOME:-${XDG_CONFIG_HOME:-$HOME/.config}/kicad}/10.0
mkdir -p "$config"
for table in sym-lib-table fp-lib-table; do
    [ ! -e "$config/$table" ] && [ ! -L "$config/$table" ] || continue
    case $table in sym-lib-table) package=kicad-library-symbols ;; *) package=kicad-library-footprints ;; esac
    source=$(pkg query '%Fp' "$package" | awk -v suffix="/template/$table" '
        length($0)>=length(suffix) && substr($0,length($0)-length(suffix)+1)==suffix {print;exit}')
    [ -n "$source" ] && [ -r "$source" ] || {
        echo "Missing KiCad library table: $table" >&2
        exit 1
    }
    (
        umask 077
        set -C
        cat "$source" >"$config/$table"
    )
done
# Keep the CLI reference matched to the installed executable, including examples'
# exact option names. These commands print help and never open a design.
mkdir -p "$repo/.build/docs"
{
    printf '# KiCad command reference\n\n'
    kicad-cli version
    while IFS= read -r command; do
        printf '\n## kicad-cli %s\n\n```text\n' "$command"
        # shellcheck disable=SC2086
        kicad-cli $command --help
        printf '```\n'
    done <<'EOF'

sch
pcb
sym
fp
jobset
sch erc
sch export bom
sch export pdf
pcb drc
pcb export gerbers
pcb export drill
pcb export pos
pcb export step
jobset run
EOF
} >"$repo/.build/docs/kicad-cli.md"
