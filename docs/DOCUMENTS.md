# Markdown and PDF workflows

The carried vis configuration includes the existing Lowdown live Markdown split:
**Space mp** toggles rendering from the unsaved buffer. The preview must not
write the source, steal its active edit buffer or leak its update process after
closing. The prior real-PTY tests are useful regression material, but the native
FreeBSD vis/Lowdown combination still needs validation.

PDF reading remains **Zathura + MuPDF**, using its GTK Wayland backend and the
copied monochrome configuration. Preserve search, page movement, links, fit to
width/window and optional recoloring. It must launch through the local file/MIME
workflow without starting an X server. See [DEVELOPMENT](DEVELOPMENT.md).
