# Retained Nostromo assets

Copied from the current OpenBSD project on 2026-11-01, preserving the default
hybrid orb, compact terminal forms and fonts/licenses. This is a standalone
asset collection; runtime installation must not reach into the older checkout.

`fonts/` contains Michroma and Azeret Mono with their OFL licenses and SHA256
record. `wallpapers/` holds only the default orb wallpaper, exported at 1080p,
1440p, 4K and 8K. The other wallpaper variants, all SVG originals and the
variants' attribution are archived outside this repository. The installed logo
and login textures use PNG too. XBM/XPM versions are historical derivatives,
not an instruction to install an X server.

`references/space-dots-original.frag` is the inspected MIT-licensed reference
shader with its original copyright header. It is not a working dwl effect.
`references/wedge_reference_extended_bar.png` is the user's supplied geometry
reference. See [DESIGN](../docs/DESIGN.md) for provenance and adaptation limits.
Nothing in this directory authorizes resurrecting the removed Arasaka texture
or replacing the default orb wallpaper.

`nostromo-orb-idle.txt` contains four fixed-size half-block frames of the same
2D orb. Vis and the live Fastfetch view use these for a small vertical float;
the wallpaper and static fetch logo keep their original artwork.
