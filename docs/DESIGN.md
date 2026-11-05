# Current design and effects references

The full acceptance list is in [PLANS](../PLANS.md). This migration preserves
black/white, Michroma UI, Azeret Mono terminal/code, the hybrid orb, existing
wallpapers and the exact later corrections to corners, rails and highlights.
It does not revive the earlier red palette or add decorative text.

## Shape and layout contract

| Element | Geometry and behavior |
| --- | --- |
| Workspace tags | Bottom-left cut only; selected tag white/black inverted; scalable |
| Status items | No frames; accepted 5% spacing/font-sized minimum; 10.5 pt Michroma |
| Foot | Body-only outline; attached white right CWD rail, square outer edge corners and unchanged long recess; centered path reads home at top to project below |
| PDF/image viewers | Body-only outline; white bottom title rail with square outer edge corners and the same long recess; Zathura and swayimg app IDs |
| Other normal clients | Body-only outline and blank rectangular white top bar |
| Fuzzel | Centered content-sized panel; white left rail with long recess; one bottom-right panel cut |
| Notifications | One bottom-right frame cut; white source label overlapping top border, inset 3.5%; label bottom-right cut and smaller left wedge |
| Login/lock input | One bottom-right cut; focus overlay larger/outside the field; joined left pair and joined right pair form two side brackets |
| Vis dashboard | Original 2D orb with gentle floating idle cycle and plain menu; no option frames |
| Dvtm | Connected panel junctions and reserved separator column; no opaque pane backgrounds |

The [wedge reference](../assets/references/wedge_reference_extended_bar.png) is
copied locally. Rails are compositor geometry; launchers/notifications are native
client geometry. The right/left/bottom recess spans the middle **80%** of each
rail, leaving **10% at each end**, with short diagonal shoulders. Its depth is
about **30% of the rail thickness**, clamped for small windows. The white fill
has no extra outline, corner highlight or glow around its outside edge. The
continuous window outline surrounds only the content body. The terminal text
stays centered on the divot midpoint within the uninterrupted white spine.
Only outer edge corners became square; the divots retain their approved shape. Top bars remain rectangular, and
the notification label retains its separate small wedge.
A GTK/Qt color file alone does not implement these shapes.
Every application panel uses **90% opacity**, including qutebrowser, PDF/image
viewers, fuzzel launchers/network managers and notifications. Foot and its terminal
applications retain native background-only alpha with solid text and pane lines.
Fuzzel and Dunst use `e6` background alpha (the nearest 8-bit value to 90%), keeping
their text, selections and frames solid. Other clients provide finished surfaces:
dwl blends their entire content at 90%, including browser pages and viewer images.
Compositor-drawn rails and outlines remain solid. Foot is exempt from the extra
multiplier, so its background does not become 81% opaque.

The compositor applies this before scene commits, covering later popups and
subsurfaces and retaining opacity when CRT motion is static/off. It reuses the
existing map-fade timer; no additional idle timer or blur pass is introduced.
Fullscreen retains dwl's protocol-required backing, and authenticated lock
surfaces retain their separate opaque backdrop. New clients float at moderate
randomized, preferably free positions; manual tiling/fullscreen keys remain explicit.

Native API references: [wlroots scene buffer opacity](https://wlroots.pages.freedesktop.org/wlroots/wlr/types/wlr_scene.h.html#wlr_scene_buffer_set_opacity)
and [Dunst Wayland color alpha](https://dunst-project.org/documentation/).

## Existing references retained

- Omarchy Weyland-Yutani CRT reference, revision
  `c88479a05e208acca0725a640ffb280e8ce26a7a`, remains an effects reference.
  Its MIT attribution is retained under assets/licenses.
- Cyberpunk 2077's site informs motion and border treatment, not a font change,
  yellow palette or additional labels.
- The user's supplied monochrome logo/reference wallpapers remain alternatives;
  the default centered orb stays. The removed Arasaka texture stays removed.
- The custom abstract insignia must still include the **NOSTROMO** wordmark;
  the default orb wallpaper must not gain a name. These are distinct designs.

## New reference: space_dots / Golden Era

Inspected the local `space_dots/` checkout and screenshot on 2026-11-01.
Origin: [vdawg-git/space_dots](https://github.com/vdawg-git/space_dots), revision
`c7775088bdb07824aeaaf41f25308c71b1f98996`.
The README calls this a look/theme reference and says media files are not
included. The linked video was **not viewed** (its MEGA embed could not be opened); motion below is inferred from
the inspected GLSL/configuration, not claimed video observation.

The useful source is [the copied original shader](../assets/references/space-dots-original.frag),
originally `.other/orig.frag`. Its header contains an MIT license, copyright
2023 Maxim Samoliuk; keep that header in derived shader code. No blanket license
is inferred for unrelated files. Its Hyprland configuration contains movement,
pop-in/out and fade curves. The supplied screenshot is warm/orange and strongly
bloomed: **borrow the screen treatment, keep Nostromo monochrome and sharp cuts**.

| Inspected effect | Native adaptation requirement |
| --- | --- |
| Scanlines and phosphor pattern | Pixel-aware monochrome texture, scaled per output; no RGB subpixel tint |
| Animated noise/grain | Bounded neutral luminance noise; do not destroy fine terminal text |
| Bright bloom/halation | White glow with preserved detail; compare a lower-cost separable/downsampled implementation |
| Analog horizontal jitter | Small controlled offset, preferably confined to transition/glitch bursts |
| Flicker | Optional low-amplitude mode; default reading mode must avoid rapid brightness modulation |
| Curvature/vignette | Keep vignette; geometric curvature off initially to preserve alignment; any future warp must include pointer/capture mapping |
| Window animations | Short motion/fade accents that respect current floating placement and focus; no copied Hyprland commands |

The reference fixes **60 Hz** and **2256×1504** in source and performs nominally
**24 × 4 = 96** bloom samples per pixel, in addition to other sampling. Its own
comment asks for disabled damage tracking to animate. Those are reference
limitations, not settings to apply to this laptop. The port must use the actual
output pixel size/scale, monotonic bounded time and output frame callbacks; it
must damage/redraw only as required and stop animation work in static/off modes.
Keep refresh rate independent from flicker amplitude. Do not force obsolete
wlroots environment variables or globally disable hardware cursors on speculation.

No Linux Hyprland config, Node/chalk-animation service, sudo/wg-quick startup,
Bluetooth applet, NetworkManager, systemd command, IP-based timezone lookup or
reference author's home path is imported as runtime configuration.

## Effects modes and rendering gate

- **Animated:** requested scan/sweep/grain and short transitions with measured
  output pacing. The actual acceptable frame rate is a hardware test.
- **Static:** texture/vignette with no continuous animation timer/redraw demand.
- **Off:** no CRT post-process; normal native composition and panel opacity remain.
- Splash: 2.4-second monochrome arrival/hold/fade after successful login.
  Login and lock use the same space_dots-derived texture and logo motion.
- Idle: bouncing logo, stationary password prompt on input, authenticated lock
  owned by the actual lock client. A fullscreen animation is never called a lock.

The actual renderer extension is in `src/dwl/crt.h` and `crt.frag`: GLES2 output
post-processing, actual output dimensions, monochrome scan/phosphor/noise,
low-cost bloom and vignette, with a shared 12 Hz animation timer. Static/off stop
animation; off restores ordinary composition. New windows have a 240 ms fade.
The reference's geometric warp and aggressive flicker are not enabled.

Host preview tools use the shipped QML, HTML, fonts and native drawing functions.
Their output goes under `.build/previews/`, outside the published source files.
Earlier compositions and SVG originals are archived outside this repository.
Native screenshots, authentication and measured power remain acceptance steps.

## Splash, login and lock animation

Animated mode is the default for the desktop, login, lock, idle and splash.
Saved static/off choices remain explicit overrides. Idle uses the shared
space_dots treatment while preserving its reflected bouncing path at 35 logical
pixels/second horizontally and 27 vertically; it does not replace that movement
with a different animation.

`src/session/space-dots.h` is the native splash/lock painter; SDDM uses
`SpaceOrb.qml` and `SpaceDots.qml`. The entrance follows the inspected
`winIn` cubic (.1, 1.1, .1, 1.1) over 1.2 seconds: a small pop-in/settle,
not large jumps or sliced logo displacement. Shared treatment includes rolling
phosphor scan phase (117 radians/second), white halation, sparse grain and
subpixel horizontal drift. Brightness variation is capped at 1%, with no RGB
tint or geometry warp. Text fields and focus/hit regions never move.

Native clients pace animation at about 30 Hz using monotonic elapsed time.
Qt uses [FrameAnimation](https://doc.qt.io/qt-6/qml-qtquick-frameanimation.html)
and quantizes effect updates to 30 Hz. The native logo is cached once (1 MiB);
grain/scan textures are tiny repeated tiles. Qt uploads reusable vector tiles
and moves their offsets rather than repainting a fullscreen Canvas. This avoids
the reference's 96-sample bloom. Actual CPU/GPU cost still needs native measurement.

`nostromo-crt static` / `off` persist the session choice read by both splash and
lock. `NOSTROMO_EFFECTS` can explicitly override a native client's startup mode.
The login greeter has its own `Effects=animated|static|off` in its root-owned
theme.conf, because it runs before choosing/authenticating a user. Both native
and QML checks exercise static/off and preserve password masking. The desktop's
separate 12 Hz GPU pass remains enabled according to its own saved mode; screenshots
of these client effects do not certify the full compositor or power consumption.

## Responsive panels and viewer titles

Fuzzel measures shaped glyph advances from its active fcft font, including the
prompt and loaded choices. The common dimension function fits content plus
padding between 240 and 720 logical pixels, further constrained by the active
output with 20-pixel outer clearance. Height follows the row count; shorter
outputs paginate whole rows. Scale/output changes recalculate dimensions. Input
and password contents never affect sizing. The 24-point row height scales with
the output; text remains 10.5-point Michroma. Host previews share this dimension
function and measure the bundled face with Pango; native fcft rendering remains
a laptop acceptance check.

Viewer bottom bars display their current Wayland title, horizontally centered
on the white spine/divot midpoint. Titles are bounded, validated UTF-8 plain
text; control characters are rejected, and long labels ellipsize in the middle.
Zathura publishes the basename and hides the duplicate statusbar by default;
Ctrl+N restores that statusbar when needed. Swayimg updates its title after an
image/selection change without a polling daemon or repeated redraw loop, and
removes the duplicate filename overlay. Counters/zoom remain available in the
image overlay. Top bars on other applications remain blank.

Verified against [Zathura settings](https://pwmt.org/projects/zathura/documentation/)
and the pinned [Swayimg 5.6 Lua API](https://github.com/artemsen/swayimg/blob/v5.6/extra/swayimg.lua).
