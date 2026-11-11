/* Nostromo server-side decorations. Cairo draws only changed rail buffers. */
#include <cairo.h>
#include "rail.h"
#include <pango/pangocairo.h>
#include <drm_fourcc.h>
#include <wlr/interfaces/wlr_buffer.h>

struct NostromoBuffer {
	struct wlr_buffer base;
	cairo_surface_t *surface;
};

static void
nostromo_buffer_destroy(struct wlr_buffer *base)
{
	struct NostromoBuffer *buffer = (struct NostromoBuffer *)base;
	cairo_surface_destroy(buffer->surface);
	free(buffer);
}

static bool
nostromo_buffer_access(struct wlr_buffer *base, uint32_t flags,
		void **data, uint32_t *format, size_t *stride)
{
	struct NostromoBuffer *buffer = (struct NostromoBuffer *)base;
	if (flags & WLR_BUFFER_DATA_PTR_ACCESS_WRITE)
		return false;
	*data = cairo_image_surface_get_data(buffer->surface);
	*stride = (size_t)cairo_image_surface_get_stride(buffer->surface);
	*format = DRM_FORMAT_ARGB8888;
	return true;
}

static void
nostromo_buffer_end(struct wlr_buffer *base)
{
	(void)base;
}

static const struct wlr_buffer_impl nostromo_buffer_impl = {
	.destroy = nostromo_buffer_destroy,
	.begin_data_ptr_access = nostromo_buffer_access,
	.end_data_ptr_access = nostromo_buffer_end,
};

/* Display data only. A client may forge its title; never open, chdir, execute
 * or inspect a path received here. Invalid UTF-8/control bytes are not rendered. */
static void
nostromo_directory(const char *title, char *label, size_t size)
{
	const char *prefix = "NOSTROMO_CWD:file://";
	char *decoded;
	size_t len;
	label[0] = '\0';
	if (!title || strncmp(title, prefix, strlen(prefix)))
		return;
	decoded = g_uri_unescape_string(title + strlen(prefix), NULL);
	if (!decoded || decoded[0] != '/' || !g_utf8_validate(decoded, -1, NULL))
		goto done;
	for (const unsigned char *p = (const unsigned char *)decoded; *p; p++)
		if (*p < 32 || *p == 127)
			goto done;
	len = strlen(decoded);
	/* Keep the tail of a long path, on a UTF-8 boundary. */
	const char *start = decoded + (len < size ? 0 : len - size + 1);
	while (((unsigned char)*start & 0xc0) == 0x80)
		start++;
	snprintf(label, size, "%s", start);
done:
	g_free(decoded);
}

static void
nostromo_padding(Client *c)
{
	int side = nostromo_rail_kind(client_get_appid(c));
	c->ntop = !c->isfullscreen && side == NOSTROMO_TOP ? 20 : 0;
	c->nright = !c->isfullscreen && side == NOSTROMO_RIGHT ? 28 : 0;
	c->nbottom = !c->isfullscreen && side == NOSTROMO_BOTTOM ? 20 : 0;
}

static void
nostromo_decoration(Client *c)
{
	struct NostromoBuffer *buffer;
	cairo_t *cr;
	char label[512];
	int scale, width, height, side;

	if (!c->rail)
		return;
	wlr_scene_node_set_enabled(&c->rail->node, !c->isfullscreen);
	if (c->isfullscreen)
		return;
	width = c->nright ? c->nright : c->geom.width;
	height = c->nright ? c->geom.height : c->nbottom ? c->nbottom : c->ntop;
	side = c->nright ? NOSTROMO_RIGHT : c->nbottom ? NOSTROMO_BOTTOM : NOSTROMO_TOP;
	scale = c->mon ? MAX(1, (int)ceil(c->mon->wlr_output->scale)) : 1;
	label[0] = '\0';
	if (side == NOSTROMO_RIGHT)
		nostromo_directory(client_get_title(c), label, sizeof(label));
	else if (side == NOSTROMO_BOTTOM)
		nostromo_viewer_title(client_get_title(c), label, sizeof(label));
	/* An unchanged decoration causes no damage and allocates no new buffer. */
	if (c->nwidth == width && c->nheight == height && c->nscale == scale && c->nside == side &&
	    !strcmp(c->nlabel, label))
		return;
	c->nwidth = width;
	c->nheight = height;
	c->nscale = scale;
	c->nside = side;
	snprintf(c->nlabel, sizeof(c->nlabel), "%s", label);
	buffer = ecalloc(1, sizeof(*buffer));
	buffer->surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32,
			width * scale, height * scale);
	if (cairo_surface_status(buffer->surface) != CAIRO_STATUS_SUCCESS) {
		cairo_surface_destroy(buffer->surface);
		free(buffer);
		return;
	}
	wlr_buffer_init(&buffer->base, &nostromo_buffer_impl, width * scale, height * scale);
	cr = cairo_create(buffer->surface);
	cairo_scale(cr, scale, scale);
	nostromo_rail_draw(cr, width, height, side, label);
	cairo_destroy(cr);
	cairo_surface_flush(buffer->surface);
	wlr_scene_buffer_set_buffer(c->rail, &buffer->base);
	wlr_scene_buffer_set_dest_size(c->rail, width, height);
	wlr_buffer_drop(&buffer->base);
}

static void
nostromo_place(Client *c, Client *parent)
{
	struct wlr_box box, best = {0};
	Client *other;
	uint64_t best_overlap = UINT64_MAX, overlap;
	int left, right, top, bottom;
	if (!c->mon || c->isfullscreen)
		return;
	box = c->mon->w;
	/* The initial client is a moderate floating window, even in a tiled tag.
 * Explicit layout keys collect it into tile/monocle later. */
	c->isfloating = 1;
	best.width = MIN(box.width, MAX(1, box.width * 62 / 100));
	best.height = MIN(box.height, MAX(1, box.height * 66 / 100));
	if (parent) {
		best.width = MIN(best.width, MAX(1, c->geom.width));
		best.height = MIN(best.height, MAX(1, c->geom.height));
		best.x = MAX(box.x, parent->geom.x + (parent->geom.width - best.width) / 2);
		best.y = MAX(box.y, parent->geom.y + (parent->geom.height - best.height) / 2);
	} else {
		for (int attempt = 0; attempt < 32; attempt++) {
			struct wlr_box sample = best;
			sample.x = box.x + (int)arc4random_uniform((uint32_t)(box.width - sample.width + 1));
			sample.y = box.y + (int)arc4random_uniform((uint32_t)(box.height - sample.height + 1));
			overlap = 0;
			wl_list_for_each(other, &clients, link) {
				if (other == c || !VISIBLEON(other, c->mon))
					continue;
				left = MAX(sample.x, other->geom.x);
				right = MIN(sample.x + sample.width, other->geom.x + other->geom.width);
				top = MAX(sample.y, other->geom.y);
				bottom = MIN(sample.y + sample.height, other->geom.y + other->geom.height);
				if (right > left && bottom > top)
					overlap += (uint64_t)(right - left) * (uint64_t)(bottom - top);
			}
			if (overlap < best_overlap) {
				best = sample;
				best_overlap = overlap;
			}
			if (!overlap)
				break;
		}
	}
	best.x = MIN(best.x, box.x + box.width - best.width);
	best.y = MIN(best.y, box.y + box.height - best.height);
	setfloating(c, 1);
	resize(c, best, 0);
	nostromo_animate_start(c);
}

static void
nostromo_layout(const Arg *arg)
{
	Client *c;
	if (!selmon)
		return;
	/* Tile and monocle are explicit actions, including previously floated apps. */
	if (((const Layout *)arg->v)->arrange)
		wl_list_for_each(c, &clients, link)
			if (VISIBLEON(c, selmon) && !c->isfullscreen)
				setfloating(c, 0);
	setlayout(arg);
}

static void
nostromo_move(const Arg *arg)
{
	Client *c = focustop(selmon);
	struct wlr_box box;
	/* The floating layout, the default, leaves every window free to move. */
	if (!c || c->isfullscreen || (!c->isfloating && selmon->lt[selmon->sellt]->arrange))
		return;
	box = c->geom;
	if (arg->i == 0) box.x -= 32;
	if (arg->i == 1) box.y += 32;
	if (arg->i == 2) box.y -= 32;
	if (arg->i == 3) box.x += 32;
	if (arg->i == 4) box.width = MAX(100, box.width - 32);
	if (arg->i == 5) box.height += 32;
	if (arg->i == 6) box.height = MAX(80, box.height - 32);
	if (arg->i == 7) box.width += 32;
	setfloating(c, 1);
	resize(c, box, 0);
}

static int nostromo_gap = 8;

static void
nostromo_tile(Monitor *m)
{
    struct wlr_box saved = m->w;
    Client *c;
    int gap = MIN(nostromo_gap, MIN(m->w.width, m->w.height) / 4);
    m->w.x += gap; m->w.y += gap;
    m->w.width -= gap; m->w.height -= gap;
    tile(m);
    m->w = saved;
    wl_list_for_each(c, &clients, link) {
        if (!VISIBLEON(c, m) || c->isfloating || c->isfullscreen) continue;
        struct wlr_box box = c->geom;
        box.width = MAX(1, box.width - gap);
        box.height = MAX(1, box.height - gap);
        resize(c, box, 0);
    }
}

static void
nostromo_gaps(const Arg *arg)
{
    Monitor *m;
    nostromo_gap = arg->i ? MAX(0, MIN(40, nostromo_gap + arg->i)) : 8;
    wl_list_for_each(m, &mons, link) arrange(m);
}

static void
nostromo_stack(const Arg *arg)
{
    Client *c = focustop(selmon), *target;
    struct wl_list *node;
    if (!c || c->isfloating || c->isfullscreen) return;
    node = arg->i > 0 ? c->link.next : c->link.prev;
    while (node != &c->link) {
        if (node != &clients) {
            target = wl_container_of(node, target, link);
            if (VISIBLEON(target, selmon) && !target->isfloating && !target->isfullscreen) {
                wl_list_remove(&c->link);
                wl_list_insert(arg->i > 0 ? &target->link : target->link.prev, &c->link);
                arrange(selmon);
                return;
            }
        }
        node = arg->i > 0 ? node->next : node->prev;
    }
}

/* H/J/K/L are 0-3. A floating window moves in that direction; a tiled one
 * moves along the stack (J/K), into the first master place (H) or out of it (L). */
static void
nostromo_shift(const Arg *arg)
{
    Client *c = focustop(selmon), *first = NULL, *other;
    if (!c || c->isfullscreen) return;
    if (c->isfloating || !selmon->lt[selmon->sellt]->arrange) {
        nostromo_move(arg);
        return;
    }
    if (arg->i == 1 || arg->i == 2) {
        nostromo_stack(&(Arg){.i = arg->i == 1 ? +1 : -1});
        return;
    }
    wl_list_for_each(other, &clients, link) {
        if (VISIBLEON(other, selmon) && !other->isfloating && !other->isfullscreen) {
            first = other;
            break;
        }
    }
    if (arg->i == 0 && c != first) zoom(NULL);
    else if (arg->i == 3 && c == first) nostromo_stack(&(Arg){.i = +1});
}

/* A floating window becomes narrower, taller, shorter or wider; for a tiled
 * one, H/L move the master border as Super+H/L do. */
static void
nostromo_resize(const Arg *arg)
{
    Client *c = focustop(selmon);
    if (!c || c->isfullscreen) return;
    if (c->isfloating || !selmon->lt[selmon->sellt]->arrange)
        nostromo_move(&(Arg){.i = arg->i + 4});
    else if (arg->i == 0 || arg->i == 3)
        setmfact(&(Arg){.f = arg->i == 0 ? -0.05f : +0.05f});
}

/* The tag beside the lowest selected one, wrapping at either end. */
static uint32_t
nostromo_neighbour(int direction)
{
    uint32_t tags = selmon->tagset[selmon->seltags];
    int i = 0;
    while (i < TAGCOUNT - 1 && !(tags & (1u << i))) i++;
    return 1u << ((i + direction + TAGCOUNT) % TAGCOUNT);
}

static void
nostromo_view(const Arg *arg)
{
    if (selmon) view(&(Arg){.ui = nostromo_neighbour(arg->i)});
}

/* The focused window moves to the neighbouring tag, and the view follows it. */
static void
nostromo_send(const Arg *arg)
{
    uint32_t target;
    if (!focustop(selmon)) return;
    target = nostromo_neighbour(arg->i);
    tag(&(Arg){.ui = target});
    view(&(Arg){.ui = target});
}

static void
nostromo_scratch(const Arg *arg)
{
    Client *c;
    (void)arg;
    if (!selmon) return;
    wl_list_for_each(c, &clients, link) {
        if (strcmp(client_get_appid(c), "nostromo.foot.scratch")) continue;
        if (VISIBLEON(c, selmon)) {
            c->tags = 0;
            arrange(selmon);
            focusclient(focustop(selmon), 1);
        } else {
            setmon(c, selmon, selmon->tagset[selmon->seltags]);
            c->tags = selmon->tagset[selmon->seltags];
            arrange(selmon);
            focusclient(c, 1);
        }
        printstatus();
        return;
    }
    const char *command[] = {"foot", "--app-id=nostromo.foot.scratch", NULL};
    spawn(&(Arg){.v = command});
}

static void
nostromo_pointer(const Arg *arg)
{
    struct timespec now;
    Client *c;
    LayerSurface *l;
    int action = arg->i % 10, step = arg->i >= 10 ? 4 : 32;
    if (locked) return;
    clock_gettime(CLOCK_MONOTONIC, &now);
    uint32_t time = (uint32_t)(now.tv_sec * 1000 + now.tv_nsec / 1000000);
    if (action < 4) {
        double x = action == 0 ? -step : action == 3 ? step : 0;
        double y = action == 1 ? step : action == 2 ? -step : 0;
        wlr_cursor_move(cursor, NULL, x, y);
        motionnotify(time, NULL, 0, 0, 0, 0);
    } else if (action < 6) {
        xytonode(cursor->x, cursor->y, NULL, &c, &l, NULL, NULL);
        if (c) focusclient(c, 1);
        uint32_t button = action == 4 ? BTN_LEFT : BTN_RIGHT;
        wlr_seat_pointer_notify_button(seat, time, button, WL_POINTER_BUTTON_STATE_PRESSED);
        wlr_seat_pointer_notify_button(seat, time, button, WL_POINTER_BUTTON_STATE_RELEASED);
    } else {
        int direction = action == 6 ? -1 : 1;
        wlr_seat_pointer_notify_axis(seat, time, WL_POINTER_AXIS_VERTICAL_SCROLL,
            direction * 15, direction * 120, WL_POINTER_AXIS_SOURCE_WHEEL,
            WL_POINTER_AXIS_RELATIVE_DIRECTION_IDENTICAL);
    }
    wlr_seat_pointer_notify_frame(seat);
}

static void
nostromo_capture(const Arg *arg)
{
    Client *c = focustop(selmon);
    char geometry[128];
    (void)arg;
    if (locked || !c) return;
    snprintf(geometry, sizeof(geometry), "%d,%d %dx%d", c->geom.x, c->geom.y,
        c->geom.width, c->geom.height);
    const char *command[] = {"nostromo-screenshot", "--geometry", geometry, NULL};
    spawn(&(Arg){.v = command});
}
