/* Native dwl geometry, also used by the host preview. */
#include <math.h>
#include <string.h>
#include <pango/pangocairo.h>
enum NostromoRail { NOSTROMO_TOP, NOSTROMO_RIGHT, NOSTROMO_BOTTOM };
static inline int nostromo_rail_kind(const char *appid)
{
	if (!appid) return NOSTROMO_TOP;
	if (!strcmp(appid, "foot") || !strcmp(appid, "nostromo.foot") ||
	    !strcmp(appid, "nostromo.foot.scratch")) return NOSTROMO_RIGHT;
	if (!strcmp(appid, "org.pwmt.zathura") || !strcmp(appid, "zathura") ||
	    !strcmp(appid, "swayimg")) return NOSTROMO_BOTTOM;
	return NOSTROMO_TOP;
}
/* Foot already blends its background; do not multiply its 0.90 alpha again.
 * Other clients expose a finished surface, so their whole content is blended.
 * Decorations and layer-shell menus retain their own opaque foregrounds. */
static inline float nostromo_client_opacity(const char *appid, float fade)
{
	return (nostromo_rail_kind(appid) == NOSTROMO_RIGHT ? 1.0f : 0.90f) * fade;
}
/* Client titles are display-only text, never markup or a filesystem authority. */
static inline void nostromo_viewer_title(const char *title, char *label, size_t size)
{
	if (!size) return;
	label[0] = '\0';
	if (!title || !g_utf8_validate(title, -1, NULL)) return;
	const char *end = title;
	for (const char *p = title; *p; p = g_utf8_next_char(p)) {
		gunichar ch = g_utf8_get_char(p);
		if (g_unichar_iscntrl(ch) || ch == 0x2028 || ch == 0x2029) return;
		const char *next = g_utf8_next_char(p);
		if ((size_t)(next-title) < size) end = next;
	}
	memcpy(label, title, (size_t)(end-title));
	label[end-title] = '\0';
}
static inline void nostromo_rail_draw(cairo_t *cr, int width, int height, int side, const char *label)
{
	PangoLayout *layout;
	PangoFontDescription *font;
	int th;
	int original_width = width, original_height = height;
	double wedge = 0, cap;
	cairo_save(cr);
	cairo_save(cr);
	if (side == NOSTROMO_BOTTOM) {
		/* The same contour, turned outward along the bottom edge. */
		cairo_matrix_t turn = {0, 1, 1, 0, 0, 0};
		cairo_transform(cr, &turn);
		int length = width; width = height; height = length;
	}
	cairo_set_source_rgb(cr, 1, 1, 1);
	if (side != NOSTROMO_TOP) {
		cap = height * 0.10;
		wedge = fmin(width * 0.3, height * 0.15);
		cairo_move_to(cr, 0, 0);
		cairo_line_to(cr, width, 0);
		cairo_line_to(cr, width, cap);
		cairo_line_to(cr, width - wedge, cap + wedge);
		cairo_line_to(cr, width - wedge, height - cap - wedge);
		cairo_line_to(cr, width, height - cap);
		cairo_line_to(cr, width, height);
		cairo_line_to(cr, 0, height);
		cairo_close_path(cr);
	} else {
		cairo_rectangle(cr, 0, 0, width, height);
	}
	cairo_fill(cr);
	cairo_restore(cr);
	width = original_width; height = original_height;
	if ((side == NOSTROMO_RIGHT || side == NOSTROMO_BOTTOM) && label && *label) {
		layout = pango_cairo_create_layout(cr);
		font = pango_font_description_from_string("Michroma 9");
		pango_layout_set_font_description(layout, font);
		pango_font_description_free(font);
		int length = side == NOSTROMO_RIGHT ? height : width;
		pango_layout_set_width(layout, MAX(1, length - 40) * PANGO_SCALE);
		pango_layout_set_ellipsize(layout, PANGO_ELLIPSIZE_MIDDLE);
		pango_layout_set_alignment(layout, PANGO_ALIGN_CENTER);
		pango_layout_set_single_paragraph_mode(layout, TRUE);
		pango_layout_set_text(layout, label, -1);
		pango_layout_get_pixel_size(layout, NULL, &th);
		cairo_set_source_rgb(cr, 0, 0, 0);
		if (side == NOSTROMO_RIGHT) {
			/* Alignment already centers inside the layout; home reads first at the top. */
			cairo_translate(cr, (width - wedge + th) / 2.0, (height - MAX(1, height - 40)) / 2.0);
			cairo_rotate(cr, 1.5707963267948966);
		} else {
			/* Horizontal title centered on the bottom divot's solid white spine. */
			PangoRectangle ink;
			pango_layout_get_pixel_extents(layout, &ink, NULL);
			if (ink.height > height - wedge - 2) {
				font = pango_font_description_from_string("Michroma 9");
				pango_font_description_set_size(font, (int)(9 * PANGO_SCALE *
				    fmax(1, height - wedge - 2) / ink.height));
				pango_layout_set_font_description(layout, font);
				pango_font_description_free(font);
				pango_layout_get_pixel_extents(layout, &ink, NULL);
			}
			cairo_translate(cr, (width - MAX(1, width - 40)) / 2.0,
			    (height - wedge - ink.height) / 2.0 - ink.y);
		}
		pango_cairo_show_layout(cr, layout);
		g_object_unref(layout);
	}
	cairo_restore(cr);
}
