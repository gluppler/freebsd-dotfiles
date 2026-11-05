# POSIX shell: temporary files and traps

```sh
#!/bin/sh
set -eu
umask 077

work=$(mktemp -d "${TMPDIR:-/tmp}/example.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM

if [ "$#" != 1 ]; then
    printf 'Usage: %s input-file\n' "$0" >&2
    exit 2
fi

sort -u "$1" >"$work/sorted"
cat "$work/sorted"
```

The exit trap runs on success and failure. The signal traps select an exit status
and let the exit trap remove the temporary directory. Quote paths and use `read -r`
when input must retain backslashes.

`mktemp` is available in FreeBSD base, although it is not specified by POSIX.
The script syntax above works with `/bin/sh`; interactive conveniences belong in
oksh configuration. Read `man sh`, `man oksh`, `man test`, `man printf` and
`man trap` where the shell builtin has its own page; otherwise search `/trap`
inside `man sh`.
