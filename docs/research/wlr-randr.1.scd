WLR-RANDR(1)

# NAME

wlr-randr - Utility to manage outputs of a Wayland compositor

# SYNOPSIS

*wlr-randr* [options...]

# DESCRIPTION

Command line interface which allows setting the size, scale, orientation of the
output for a screen. This utility requires the compositor to implement the
*wlr-output-management* protocol.

# OPTIONS

*--help*
	Show help message.

*--dryrun*
	Performs all the actions specified except that no changes are applied.

*--json*
	Print current state as JSON.

*--output* <name>
	Selects an output to reconfigure. This option must be set when making
	making changes to the output using below options.

*--on*
	Enables the selected output.

*--off*
	Disables the selected output.

*--mode* | *--custom-mode* <width>x<height>[@<refresh>Hz]
	Set output resolution and, optionally, refresh rate.

*--pos* <x>,<y>
	Position the output with absolute layout coordinates.

*--left-of*, *--right-of*, *--above*, *--below* <another-output>
	Position the output relative to an existing output. Absolute positioning
	via *--pos* overwrites a previously established relative position and
	vice versa. The last positioning option passed on the command-line takes
	precedence.

*--transform* normal|90|180|270|flipped|flipped-90|flipped-180|flipped-270
	Transform the output by rotating it following the provided value.

*--scale* <factor>
	Scales the specified output by the specified scale factor. An integer is
	recommended, but fractional values are also supported. If a fractional
	value are specified, be warned that it is not possible to faithfully
	represent the contents of your windows - they will be rendered at the
	next highest integer scale factor and downscaled.

# SEE ALSO

_xrandr_(1)

# AUTHORS

Maintained by Simon Ser <contact@emersion.fr>. For more information about
wlr-randr development, see <https://gitlab.freedesktop.org/emersion/wlr-randr>.
