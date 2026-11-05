/* The overlay is drawn above real GTK input widgets; authentication stays in PAM. */
#include <math.h>
#include "art.h"

struct NostromoLockTheme {
	struct Window *window;
	GtkWidget *canvas;
	cairo_surface_t *orb;
	gint64 start;
	guint timer;
	int effects; /* 0 off, 1 static, 2 animated */
};

static gboolean
nostromo_lock_draw(GtkWidget *widget, cairo_t *cr, gpointer data)
{
    struct NostromoLockTheme *theme = data;
    struct Window *w = theme->window;
    int x = 0, y = 0, fw = 0, fh = 0;
    if (gtk_widget_get_mapped(w->input_field) &&
        gtk_widget_translate_coordinates(w->input_field, widget, 0, 0, &x, &y)) {
        fw = gtk_widget_get_allocated_width(w->input_field);
        fh = gtk_widget_get_allocated_height(w->input_field);
    }
    nostromo_lock_art(cr, theme->orb, gtk_widget_get_allocated_width(widget),
        gtk_widget_get_allocated_height(widget),
        (g_get_monotonic_time() - theme->start) / 1000000.0, theme->effects,
        gtklock->hidden, x, y, fw, fh, gtk_widget_has_focus(w->input_field));
    return FALSE;
}

static gboolean
nostromo_lock_tick(gpointer data)
{
	struct NostromoLockTheme *theme = data;
	gtk_widget_queue_draw(theme->canvas);
	return G_SOURCE_CONTINUE;
}

static void
nostromo_lock_theme_free(gpointer data)
{
	struct NostromoLockTheme *theme = data;
	if (theme->timer) g_source_remove(theme->timer);
	if (theme->orb) cairo_surface_destroy(theme->orb);
	g_free(theme);
}

static void
nostromo_lock_theme(struct Window *w)
{
	struct NostromoLockTheme *theme = g_new0(struct NostromoLockTheme, 1);
	GdkRectangle geometry;
	theme->window = w;
	theme->start = g_get_monotonic_time();
	theme->effects = nostromo_space_mode();
	theme->orb = nostromo_space_logo("/usr/local/share/nostromo/nostromo-orb.png");
	theme->canvas = gtk_drawing_area_new();
	gtk_widget_set_hexpand(theme->canvas, TRUE);
	gtk_widget_set_vexpand(theme->canvas, TRUE);
	gtk_overlay_add_overlay(GTK_OVERLAY(w->overlay), theme->canvas);
	gtk_overlay_set_overlay_pass_through(GTK_OVERLAY(w->overlay), theme->canvas, TRUE);
	g_signal_connect(theme->canvas, "draw", G_CALLBACK(nostromo_lock_draw), theme);
	g_object_set_data_full(G_OBJECT(theme->canvas), "nostromo-theme", theme, nostromo_lock_theme_free);
	gdk_monitor_get_geometry(w->monitor, &geometry);
	gtk_widget_set_size_request(w->input_field, MIN(380, MAX(140, geometry.width - 80)), 48);
	/* GTK applies the output scale. No global 1080p/4K coordinate assumption. */
	gtk_widget_set_margin_top(w->window_box, MAX(0, geometry.height / 5));
	if (theme->effects == 2)
		theme->timer = g_timeout_add(1000 / NOSTROMO_EFFECT_FPS, nostromo_lock_tick, theme);
}
