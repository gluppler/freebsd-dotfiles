/* ISC: Copyright (c) 2026 Nostromo contributors. Provided without warranty. */
#ifndef NOSTROMO_NOTIFICATION_H
#define NOSTROMO_NOTIFICATION_H
#include <math.h>
#include <string.h>
#include <pango/pangocairo.h>
#include "draw.h"

/* Only the notification outline uses cuts. Icons/progress keep upstream paths. */
static inline void nostromo_frame(cairo_t *c, double x, double y, double w,
    double h, double cut, double scale, enum corner_pos corners)
{
    cut = fmax(0, fmin(cut, fmin(w, h) / 2));
    double tl = corners & C_TOP_LEFT ? cut : 0;
    double tr = corners & C_TOP_RIGHT ? cut : 0;
    double bl = corners & C_BOT_LEFT ? cut : 0;
    double br = corners & C_BOT_RIGHT ? cut : 0;
    cairo_move_to(c, (x + tl) * scale, y * scale);
    cairo_line_to(c, (x + w - tr) * scale, y * scale);
    cairo_line_to(c, (x + w) * scale, (y + tr) * scale);
    cairo_line_to(c, (x + w) * scale, (y + h - br) * scale);
    cairo_line_to(c, (x + w - br) * scale, (y + h) * scale);
    cairo_line_to(c, (x + bl) * scale, (y + h) * scale);
    cairo_line_to(c, x * scale, (y + h - bl) * scale);
    cairo_line_to(c, x * scale, (y + tl) * scale);
    cairo_close_path(c);
}

static inline PangoLayout *nostromo_source(PangoContext *context,
    const PangoFontDescription *font, const char *appname)
{
    PangoLayout *label = pango_layout_new(context);
    char *valid = g_utf8_make_valid(appname ? appname : "", -1);
    for (char *p = valid; *p; p++) if ((unsigned char)*p < 32 || *p == 127) *p = ' ';
    g_strstrip(valid);
    char *short_name = g_utf8_substring(valid, 0, MIN(48, g_utf8_strlen(valid, -1)));
    const char *name = *short_name && strcmp(short_name, "unknown") ? short_name : "NOTIF";
    pango_layout_set_font_description(label, font);
    pango_layout_set_single_paragraph_mode(label, TRUE);
    pango_layout_set_ellipsize(label, PANGO_ELLIPSIZE_END);
    pango_layout_set_auto_dir(label, FALSE);
    pango_layout_set_text(label, name, -1); /* App names are text, never markup. */
    g_free(short_name);
    g_free(valid);
    return label;
}

static inline int nostromo_source_height(PangoLayout *label, double scale)
{
    int h;
    pango_layout_get_pixel_size(label, NULL, &h);
    return (int)ceil(h / scale) + 8;
}

static inline void nostromo_source_draw(cairo_t *c, PangoLayout *label, int width, double scale)
{
    int w, h;
    double x = round(width * .035 * scale);
    int available = MAX(1, (int)(width * .60) - 24);
    pango_layout_set_width(label, (int)round(available * scale * PANGO_SCALE));
    pango_layout_get_pixel_size(label, &w, &h);
    cairo_save(c);
    double height=nostromo_source_height(label,scale)*scale;
    double right=x+fmin(width*scale-x,w+24*scale);
    double cut=fmin(height/4,(right-x)/4), depth=fmin(4*scale,height/8);
    double mid=height/2, half=height/6;
    cairo_move_to(c,x,0); cairo_line_to(c,right,0);
    cairo_line_to(c,right,height-cut); cairo_line_to(c,right-cut,height);
    cairo_line_to(c,x,height); cairo_line_to(c,x,mid+half+depth);
    cairo_line_to(c,x+depth,mid+half); cairo_line_to(c,x+depth,mid-half);
    cairo_line_to(c,x,mid-half-depth); cairo_close_path(c);
    cairo_set_source_rgb(c, 1, 1, 1);
    cairo_fill(c);
    cairo_move_to(c, x + 12 * scale, 4 * scale);
    cairo_set_source_rgb(c, 0, 0, 0);
    pango_cairo_show_layout(c, label);
    cairo_restore(c);
}
#endif
