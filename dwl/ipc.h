/* ISC: Copyright (c) 2026 Nostromo contributors. Provided without warranty.
 * Implementation of dwlb's versioned dwl-ipc-unstable-v2 protocol. */
#include "dwl-ipc-unstable-v2-protocol.h"

struct NostromoIPC {
    struct wl_list link;
    struct wl_resource *resource;
    Monitor *monitor;
};
static struct wl_list nostromo_subscriptions;

static void
nostromo_ipc_send(struct NostromoIPC *subscription)
{
    Monitor *m = subscription->monitor;
    struct wl_resource *r = subscription->resource;
    Client *c, *selected;
    if (!m) return;
    selected = focustop(m);
    zdwl_ipc_output_v2_send_active(r, m == selmon);
    for (unsigned int tag = 0; tag < TAGCOUNT; tag++) {
        unsigned int count = 0, state = m->tagset[m->seltags] & (1u << tag) ? 1 : 0;
        wl_list_for_each(c, &clients, link) {
            if (c->mon != m || !(c->tags & (1u << tag))) continue;
            count++;
            if (c->isurgent) state |= 2;
        }
        zdwl_ipc_output_v2_send_tag(r, tag, state, count,
            selected && (selected->tags & (1u << tag)) ? 1 : 0);
    }
    zdwl_ipc_output_v2_send_layout(r, (uint32_t)(m->lt[m->sellt] - layouts));
    zdwl_ipc_output_v2_send_layout_symbol(r, m->ltsymbol);
    zdwl_ipc_output_v2_send_title(r, selected ? client_get_title(selected) : "");
    zdwl_ipc_output_v2_send_appid(r, selected ? client_get_appid(selected) : "");
    if (wl_resource_get_version(r) >= 2) {
        zdwl_ipc_output_v2_send_fullscreen(r, selected && selected->isfullscreen);
        zdwl_ipc_output_v2_send_floating(r, selected && selected->isfloating);
    }
    zdwl_ipc_output_v2_send_frame(r);
}

static void
nostromo_ipc_update(void)
{
    struct NostromoIPC *subscription;
    wl_list_for_each(subscription, &nostromo_subscriptions, link)
        nostromo_ipc_send(subscription);
}

static void
nostromo_ipc_removed(Monitor *m)
{
    struct NostromoIPC *subscription;
    wl_list_for_each(subscription, &nostromo_subscriptions, link)
        if (subscription->monitor == m) subscription->monitor = NULL;
}

static void
nostromo_ipc_release(struct wl_client *client, struct wl_resource *resource)
{
    (void)client;
    wl_resource_destroy(resource);
}

static void
nostromo_ipc_destroy(struct wl_resource *resource)
{
    struct NostromoIPC *subscription = wl_resource_get_user_data(resource);
    wl_list_remove(&subscription->link);
    free(subscription);
}

static void
nostromo_ipc_tags(struct wl_client *client, struct wl_resource *resource,
    uint32_t tags, uint32_t toggle)
{
    struct NostromoIPC *subscription = wl_resource_get_user_data(resource);
    Monitor *m = subscription->monitor;
    (void)client;
    if (locked || !m || !(tags &= TAGMASK)) return;
    if (toggle) m->seltags ^= 1;
    m->tagset[m->seltags] = tags;
    arrange(m);
    focusclient(focustop(selmon), 1);
    printstatus();
}

static void
nostromo_ipc_client_tags(struct wl_client *client, struct wl_resource *resource,
    uint32_t and_tags, uint32_t xor_tags)
{
    struct NostromoIPC *subscription = wl_resource_get_user_data(resource);
    Monitor *m = subscription->monitor;
    Client *c;
    uint32_t tags;
    (void)client;
    if (locked || !m || !(c = focustop(m))) return;
    tags = ((c->tags & and_tags) ^ xor_tags) & TAGMASK;
    if (!tags) return;
    c->tags = tags;
    arrange(m);
    focusclient(focustop(selmon), 1);
    printstatus();
}

static void
nostromo_ipc_layout(struct wl_client *client, struct wl_resource *resource,
    uint32_t index)
{
    struct NostromoIPC *subscription = wl_resource_get_user_data(resource);
    Monitor *m = subscription->monitor;
    Client *c;
    (void)client;
    if (locked || !m || index >= LENGTH(layouts)) return;
    m->lt[m->sellt] = &layouts[index];
    if (layouts[index].arrange)
        wl_list_for_each(c, &clients, link)
            if (VISIBLEON(c, m) && !c->isfullscreen) setfloating(c, 0);
    arrange(m);
    printstatus();
}

static const struct zdwl_ipc_output_v2_interface nostromo_output_impl = {
    .release = nostromo_ipc_release,
    .set_tags = nostromo_ipc_tags,
    .set_client_tags = nostromo_ipc_client_tags,
    .set_layout = nostromo_ipc_layout,
};

static void
nostromo_ipc_output(struct wl_client *client, struct wl_resource *manager,
    uint32_t id, struct wl_resource *output_resource)
{
    struct wlr_output *output = wlr_output_from_resource(output_resource);
    struct NostromoIPC *subscription = calloc(1, sizeof(*subscription));
    if (!subscription) { wl_client_post_no_memory(client); return; }
    subscription->resource = wl_resource_create(client, &zdwl_ipc_output_v2_interface,
        wl_resource_get_version(manager), id);
    if (!subscription->resource) { free(subscription); wl_client_post_no_memory(client); return; }
    subscription->monitor = output ? output->data : NULL;
    wl_list_insert(&nostromo_subscriptions, &subscription->link);
    wl_resource_set_implementation(subscription->resource, &nostromo_output_impl,
        subscription, nostromo_ipc_destroy);
    nostromo_ipc_send(subscription);
}

static const struct zdwl_ipc_manager_v2_interface nostromo_manager_impl = {
    .release = nostromo_ipc_release,
    .get_output = nostromo_ipc_output,
};

static void
nostromo_ipc_bind(struct wl_client *client, void *data, uint32_t version, uint32_t id)
{
    struct wl_resource *resource = wl_resource_create(client,
        &zdwl_ipc_manager_v2_interface, MIN(version, 2), id);
    (void)data;
    if (!resource) { wl_client_post_no_memory(client); return; }
    wl_resource_set_implementation(resource, &nostromo_manager_impl, NULL, NULL);
    zdwl_ipc_manager_v2_send_tags(resource, TAGCOUNT);
    for (size_t i = 0; i < LENGTH(layouts); i++)
        zdwl_ipc_manager_v2_send_layout(resource, layouts[i].symbol);
}
