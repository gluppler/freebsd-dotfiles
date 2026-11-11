/* Native lock geometry; coordinates come from real GTK input allocation. */
#include <math.h>
#include "space-dots.h"
static double
nostromo_bounce(double elapsed, double extent, double speed)
{
	double phase;
	if (extent <= 0)
		return 0;
	phase = fmod(elapsed * speed, extent * 2);
	return phase <= extent ? phase : extent * 2 - phase;
}

static inline void nostromo_lock_art(cairo_t *cr, cairo_surface_t *orb, int width, int height,
    double seconds, int effects, int hidden, int x, int y, int fw, int fh, int focused)
{
	double size = fmin(230, fmin(width, height) * 0.24);
	double ox = (width - size) / 2, oy = height * 0.33 - size / 2;
	double cut, gap, arm, pulse = effects == 2 ? 0.5 + 0.5 * sin(seconds * 4) : 1;
	if (hidden && effects == 2) {
		ox = 24 + nostromo_bounce(seconds, width - size - 48, 35);
		oy = 24 + nostromo_bounce(seconds, height - size - 48, 27);
	}
	nostromo_space_orb(cr, orb, ox, oy, size, seconds, effects);
	if (!hidden && fw > 0 && fh > 0) {
		cut = fmin(fh * 0.24, 14);
		cairo_set_source_rgb(cr, 1, 1, 1);
		cairo_set_line_width(cr, 1.5);
		cairo_move_to(cr, x, y);
		cairo_line_to(cr, x + fw, y);
		cairo_line_to(cr, x + fw, y + fh - cut);
		cairo_line_to(cr, x + fw - cut, y + fh);
		cairo_line_to(cr, x, y + fh);
		cairo_close_path(cr);
		cairo_stroke(cr);
		if (focused) {
			gap = 7 + 2 * pulse;
			arm = fmin(fw * 0.18, fh * 0.65);
			cairo_set_source_rgba(cr, 1, 1, 1, 0.6 + pulse * 0.4);
			cairo_set_line_width(cr, 2.5);
			/* Two open brackets; each side joins both corners vertically. */
			cairo_move_to(cr, x - gap + arm, y - gap);
			cairo_line_to(cr, x - gap, y - gap);
			cairo_line_to(cr, x - gap, y + fh + gap);
			cairo_line_to(cr, x - gap + arm, y + fh + gap);
			cairo_move_to(cr, x + fw + gap - arm, y - gap);
			cairo_line_to(cr, x + fw + gap, y - gap);
			cairo_line_to(cr, x + fw + gap, y + fh + gap - cut);
			cairo_line_to(cr, x + fw + gap - cut, y + fh + gap);
			cairo_line_to(cr, x + fw + gap - arm, y + fh + gap);
			cairo_stroke(cr);
		}
	}
	nostromo_space_texture(cr, width, height, seconds, effects);
}
