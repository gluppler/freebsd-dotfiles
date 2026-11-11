# Native Wayland browser configuration.
import os
from pathlib import Path

config.load_autoconfig()  # Preserve the user's saved per-site permissions.
c.qt.force_platform = "wayland"
c.fonts.default_family = ["Michroma", "sans-serif"]
c.fonts.default_size = "10.5pt"
c.fonts.web.family.fixed = "Azeret Mono"
c.fonts.web.family.sans_serif = "Michroma"
c.fonts.web.family.standard = "Michroma"
c.tabs.position = "top"
c.tabs.show = "multiple"
c.content.autoplay = False

data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
if not data.is_absolute():
    raise ValueError("XDG_DATA_HOME must be an absolute path")
start = (data / "nostromo/start/index.html").as_uri()
c.url.start_pages = [start]
c.url.default_page = start
c.editor.command = ["foot", "-e", "vis", "+{line}", "{file}"]

# Distinguish focus and modes with inversion and greys.
for name in (
    "completion.odd.bg", "completion.even.bg", "completion.category.bg",
    "contextmenu.menu.bg", "downloads.bar.bg", "keyhint.bg", "prompts.bg",
    "statusbar.normal.bg", "statusbar.command.bg", "statusbar.caret.bg",
    "tabs.bar.bg", "tabs.odd.bg", "tabs.even.bg", "tabs.pinned.odd.bg",
    "tabs.pinned.even.bg", "tooltip.bg",
):
    config.set("colors." + name, "#000000")
for name in (
    "completion.fg", "completion.category.fg", "completion.match.fg",
    "contextmenu.menu.fg", "keyhint.fg", "keyhint.suffix.fg", "prompts.fg",
    "statusbar.normal.fg", "statusbar.command.fg", "statusbar.caret.fg",
    "tabs.odd.fg", "tabs.even.fg", "tabs.pinned.odd.fg", "tabs.pinned.even.fg",
    "tooltip.fg",
):
    config.set("colors." + name, "#ffffff")
for name in (
    "completion.item.selected", "contextmenu.selected", "prompts.selected",
    "statusbar.insert", "statusbar.passthrough", "tabs.selected.odd",
    "tabs.selected.even", "tabs.pinned.selected.odd", "tabs.pinned.selected.even",
    "statusbar.caret.selection", "downloads.start", "downloads.stop",
    "downloads.error", "hints",
):
    config.set("colors." + name + ".bg", "#ffffff")
    config.set("colors." + name + ".fg", "#000000")
for level in ("info", "warning", "error"):
    config.set("colors.messages." + level + ".bg", "#000000")
    config.set("colors.messages." + level + ".fg", "#ffffff")
    config.set("colors.messages." + level + ".border", "#ffffff")
for suffix in ("success.http", "success.https", "warn", "error", "hover"):
    config.set("colors.statusbar.url." + suffix + ".fg", "#ffffff")
c.colors.statusbar.private.bg = "#333333"
c.colors.statusbar.private.fg = "#ffffff"
c.colors.statusbar.command.private.bg = "#333333"
c.colors.statusbar.command.private.fg = "#ffffff"
c.colors.webpage.preferred_color_scheme = "dark"
c.colors.statusbar.url.fg = "#cccccc"
c.colors.completion.item.selected.border.top = "#ffffff"
c.colors.completion.item.selected.border.bottom = "#ffffff"
c.colors.completion.item.selected.match.fg = "#000000"
c.colors.completion.category.border.top = "#666666"
c.colors.completion.category.border.bottom = "#666666"
c.colors.hints.match.fg = "#555555"
c.colors.tabs.indicator.start = "#666666"
c.colors.tabs.indicator.stop = "#ffffff"
c.colors.tabs.indicator.error = "#aaaaaa"

config.bind("<Ctrl-g>", "set-cmd-text -s :open")
config.bind("<Ctrl-Shift-h>", "tab-prev")
config.bind("<Ctrl-Shift-l>", "tab-next")
config.bind("<Ctrl-Shift-Return>", "open -t")
# Default f/F hints, j/k scrolling, o/O, / and tab controls remain available.
