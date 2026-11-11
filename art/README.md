# Nostromo artwork

Copied from the current OpenBSD project on 2026-11-01, preserving the default
hybrid orb and its compact terminal forms. This is a standalone collection;
runtime installation must not reach into the older checkout.

- `nostromo-orb.png` is the login, lock and start-page logo. Its FreeBSD glyph
  comes from Font Logos (Nerd Fonts 3.0.2, U+F30C); the notice and the FreeBSD
  trademark statement are in `licenses/font-logos.txt`.
- `loader-orb.png` is the boot loader's logo.
- `nostromo-orb-small.txt` is the static fetch logo. `nostromo-orb-idle.txt`
  contains four fixed-size half-block frames of the same 2D orb; vis and the
  live Fastfetch view use them for a small vertical float.

[Fonts](../fonts) holds Michroma and Azeret Mono with their OFL licenses and
SHA256 record. [Wallpapers](../wallpapers) holds only the default orb wallpaper,
exported at 1080p, 1440p, 4K and 8K. The other wallpaper variants, all SVG
originals and the variants' attribution are archived outside this repository.

[Design references](../docs/design) keep the inspected MIT-licensed
`space-dots-original.frag`, with its original copyright header, and the user's
supplied wedge geometry reference. The shader is not a working dwl effect. See
[DESIGN](../docs/DESIGN.md) for provenance and adaptation limits. Nothing here
authorizes resurrecting the removed Arasaka texture or replacing the default orb
wallpaper.
