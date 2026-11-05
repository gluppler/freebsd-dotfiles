# Read-only upstream research snapshots

These small port definitions/manuals were downloaded from the official FreeBSD
and upstream project repositories on 2026-11-01 to verify migration decisions.
They are **not runtime files, install scripts, an approved package manifest or
a source-build lock**. Do not execute them as part of the laptop setup.

The source URLs and version observations are recorded in [SOURCES](../SOURCES.md).
`qutebrowser-configdata.yml` is specifically from upstream v3.7.0 and is used by
the static option-name test; `foot.ini.5.scd` is from 1.28.0. Port Makefiles are
snapshots of FreeBSD main and may differ from installed quarterly packages.

The luakit and ly recipes record considered alternatives. Qutebrowser is the
chosen browser, and a text-mode login does not replace the required graphical
login. Retaining research does not install those alternative applications.
