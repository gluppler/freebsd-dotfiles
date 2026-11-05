# Electronics and PCB design

Choose **PCB DESIGN** in the launcher to open KiCad. **PCB WORKFLOW** opens the
keyboard menu for checks, fabrication exports, InteractiveHtmlBom and STEP export.
The build enables GTK/Wayland and EGL. The wrapper selects `GDK_BACKEND=wayland`;
no X server is started for KiCad.

The pinned quarterly suite is **KiCad 10.0.6**, with matching official symbols,
footprints, 3D models, project templates and English HTML manuals. The 3D-model
package alone occupies about 3.37 GB on disk. These libraries add no idle service.
Installation copies the packaged global library tables only when the user has
none; existing tables and project-specific libraries stay intact.

## Design through fabrication

1. Create a project from KiCad or an installed template. Keep its `.kicad_pro`,
   root `.kicad_sch` and `.kicad_pcb` together with the same basename. Save them
   before using command-line exports; unsaved GUI edits are not visible to CLI tools.
2. Capture the schematic, assign footprints and run ERC. Add manufacturer part
   numbers and other purchasing fields to symbols as needed. Keep custom symbols,
   footprints and model paths in the project and track them in Git.
3. Use the built-in ngspice simulator for circuits with appropriate SPICE models.
   Install trusted vendor models per project; a symbol alone is not a simulation
   model. The shared simulator runs without GNU Readline or an X11 CLI.
4. Set the PCB stackup, net classes, clearances, trace widths, drill sizes and
   design rules for the board and the chosen fabricator. Inspect the 3D view.
   Use PCB Calculator for electrical/mechanical estimates.
5. Run `nostromo-eda check path/to/board.kicad_pro`. ERC and DRC, including
   schematic parity, must pass. Reports remain in a new `pcb-output.*` directory
   even when checks fail. Refill and save zones in the PCB editor first.
6. Run `nostromo-eda manufacture path/to/board.kicad_pro`. It checks again and
   exports all copper layers, masks, paste, silkscreens, board outline, Excellon
   drills, a CSV BOM, positions in millimetres, a monochrome schematic PDF and
   an interactive assembly page. Each run gets a fresh directory; old outputs
   and source designs are never overwritten.
7. Open the Gerbers and drills in GerbView. Inspect outline, layer order, plated
   versus non-plated holes and origin. Confirm position orientation, units,
   bottom-side convention, DNP parts and BOM fields with the fabricator before
   sending files. The exports make no supplier-specific assumptions.

`nostromo-eda step path/to/board.kicad_pro` exports a STEP assembly for enclosure
work. KiCad's native Jobsets support additional repeatable outputs and variants;
store a project's jobset in Git and run it with `kicad-cli jobset run`. Use that
when a project needs different fabrication rules instead of editing global scripts.

## Assembly plugin and dependency choices

InteractiveHtmlBom is pinned to commit
`d1eb5b79a52a2ddc1ce270b63920346463c19b05` and SHA256-checked during installation.
`nostromo-eda ibom path/to/board.kicad_pro` creates a self-contained `ibom.html`:
open it in qutebrowser for board/BOM cross-highlighting and assembly checklists.
The workflow uses the plugin's supported terminal interface and KiCad's `pcbnew`
bindings. Its files and MIT license remain together under the generated build
directory; no plugin runs with root privileges.

The lean KiCad variant retains the native tools and Python board bindings but
disables the embedded wxPython console and legacy wxPython plugin dialogs.
This avoids NumPy/OpenBLAS/GCC and the toolkit's optional WebKit/media stack.
KiCad's IPC interface remains available; additional plugins need their own
dependency review before installing them through PCM. The recipe also omits
OpenCASCADE's Draw/Qt/VTK applications and Poppler's optional PDF-signature engines.
It keeps geometry, STEP and model conversion, simulation and PDF import/export.
libsecret retains its encrypted backend; the two exact additional GNU library
exceptions are recorded in [PACKAGES](PACKAGES.md).

The full native FreeBSD build and a real design still need acceptance on the
laptop: launch the editors on Wayland, load the standard libraries, simulate a
small circuit, run ERC/DRC, export files, inspect GerbView/3D and open the assembly
page. Host command tests do not establish KiCad's runtime compatibility.

## Offline help

Choose **DOCS → KICAD MANUALS**, or `nostromo-eda docs`. This opens the installed
version's English manuals without a web request. Schematic, PCB, GerbView,
calculator, drawing-sheet and getting-started books are available. **KICAD CLI**
opens a formatted terminal reference generated from the installed command's
own help, including the commands used by this workflow.

Sources: [KiCad manual](https://docs.kicad.org/10.0/en/kicad/kicad.html),
[CLI reference](https://docs.kicad.org/10.0/en/cli/cli.html),
[build options](https://dev-docs.kicad.org/en/build/compile-options/),
[IPC plugins](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/),
[InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom).
