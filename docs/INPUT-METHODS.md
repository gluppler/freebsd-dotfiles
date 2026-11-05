# English, Japanese and Korean on Wayland

The physical keyboard remains US. Super+Ctrl+Space cycles US → JP → KR;
LANGUAGE opens the direct chooser. `nostromo-language` reads the actual running
engine and verifies a change; it reports `--` if the input-method service is
unavailable. It does not pretend that changing a keyboard layout supplies
Japanese conversion.

The selected engines are fcitx5 `keyboard-us`, Anthy and Hangul, with shared
input state across applications. FreeBSD packages are `fcitx5`,
`ja-fcitx5-anthy`, `ko-fcitx5-hangul` and a CJK fallback font. The installer provisions these through the dependency gate. Additional languages need an installed
engine plus entries in `nostromo/languages` and `fcitx5/profile`.

dwl 0.9 implements input-method-v2 and text-input-v3. foot uses that path;
modern GTK and Qt 6.8.2+ can also use their native Wayland input contexts.
The session must leave `GTK_IM_MODULE` and `QT_IM_MODULE` unset, force the
native Wayland display backends and start fcitx5 with its X connection disabled.
This follows the [fcitx Wayland integration guidance](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland).

The theme retains Michroma; CJK characters need a fallback face rather than
changing the Latin font. Config files are implemented; native installation,
candidate-panel positioning, conversion, deletion, focus transfer and reconnect
must be tested in foot/vis, qutebrowser and GTK clients before this workflow is
declared complete. `fcitx5-remote` acknowledgement proves a selected engine,
not successful composition in every application.
