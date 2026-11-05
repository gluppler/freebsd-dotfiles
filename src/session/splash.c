/* Brief native layer-shell splash. It never grabs the keyboard or serves as a lock. */
#include <gtk/gtk.h>
#include <gtk-layer-shell.h>
#include <math.h>
#include <string.h>
#include "splash-art.h"

static cairo_surface_t *logo;
static gint64 started;
static GPtrArray *windows;
static gboolean animated=TRUE, effects=TRUE;

static gboolean draw(GtkWidget *widget, cairo_t *cr, gpointer data) {
    double t=(g_get_monotonic_time()-started)/1000000.0;
    int width=gtk_widget_get_allocated_width(widget), height=gtk_widget_get_allocated_height(widget);
    nostromo_splash_art(cr,logo,width,height,t,animated,effects);
    return FALSE;
}
static gboolean tick(gpointer data) {
    if (g_get_monotonic_time()-started>=NOSTROMO_SPLASH_SECONDS*1000000) { gtk_main_quit(); return G_SOURCE_REMOVE; }
    for (guint i=0;i<windows->len;i++) gtk_widget_queue_draw(g_ptr_array_index(windows,i));
    return G_SOURCE_CONTINUE;
}
static gboolean finish(gpointer data) { gtk_main_quit(); return G_SOURCE_REMOVE; }
static void add_monitor(GdkDisplay *display, GdkMonitor *monitor, gpointer data) {
    GtkWidget *window=gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_widget_set_app_paintable(window,TRUE);
    GdkVisual *visual=gdk_screen_get_rgba_visual(gtk_widget_get_screen(window));
    if (visual) gtk_widget_set_visual(window,visual);
    gtk_layer_init_for_window(GTK_WINDOW(window));
    gtk_layer_set_namespace(GTK_WINDOW(window),"nostromo-splash");
    gtk_layer_set_monitor(GTK_WINDOW(window),monitor);
    gtk_layer_set_layer(GTK_WINDOW(window),GTK_LAYER_SHELL_LAYER_OVERLAY);
    gtk_layer_set_keyboard_mode(GTK_WINDOW(window),GTK_LAYER_SHELL_KEYBOARD_MODE_NONE);
    gtk_layer_set_exclusive_zone(GTK_WINDOW(window),-1);
    for (int edge=0;edge<GTK_LAYER_SHELL_EDGE_ENTRY_NUMBER;edge++) gtk_layer_set_anchor(GTK_WINDOW(window),edge,TRUE);
    g_signal_connect(window,"draw",G_CALLBACK(draw),NULL);
    gtk_widget_show_all(window);
    cairo_region_t *empty=cairo_region_create();
    gdk_window_input_shape_combine_region(gtk_widget_get_window(window),empty,0,0);
    cairo_region_destroy(empty);
    g_object_ref(window);
    g_ptr_array_add(windows,window);
}
int main(int argc,char **argv) {
    if (argc!=1) return 2;
    if (!gtk_init_check(&argc,&argv) || !gtk_layer_is_supported()) return 1;
    char *path=g_build_filename(g_get_user_data_dir(),"nostromo","nostromo-orb.png",NULL);
    logo=nostromo_space_logo(path); g_free(path);
    if (!logo) return 1;
    int mode=nostromo_space_mode();
    animated=mode==2;effects=mode!=0;
    windows=g_ptr_array_new_with_free_func(g_object_unref);
    started=g_get_monotonic_time();
    GdkDisplay *display=gdk_display_get_default();
    for (int i=0;i<gdk_display_get_n_monitors(display);i++) add_monitor(display,gdk_display_get_monitor(display,i),NULL);
    g_signal_connect(display,"monitor-added",G_CALLBACK(add_monitor),NULL);
    if (animated) g_timeout_add(1000/NOSTROMO_EFFECT_FPS,tick,NULL); else g_timeout_add((guint)(NOSTROMO_SPLASH_SECONDS*1000),finish,NULL);
    gtk_main();
    for (guint i=0;i<windows->len;i++) gtk_widget_destroy(g_ptr_array_index(windows,i));
    g_ptr_array_unref(windows); cairo_surface_destroy(logo);
    return 0;
}
