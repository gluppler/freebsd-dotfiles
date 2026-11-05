#!/usr/bin/env python3
"""Run dwl's patched hit test with client, rail and empty scene nodes."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/'.build/cross-dwl/dwl.c').read_text()
hit_test = source[source.index('void\nxytonode('):source.index('\nvoid\nzoom(')]
stubs = r'''
#include <assert.h>
#include <stddef.h>
typedef int Client;
typedef int LayerSurface;
enum { NUM_LAYERS = 3, LyrIMPopup = 2, WLR_SCENE_NODE_BUFFER = 1 };
struct wlr_surface { int client; };
struct wlr_scene_surface { struct wlr_surface *surface; };
struct wlr_scene_node { int type; struct wlr_scene_surface *surface; };
struct wlr_scene_tree { struct wlr_scene_node node; };
struct wlr_scene_buffer { struct wlr_scene_node node; };
static struct wlr_scene_tree trees[NUM_LAYERS];
static struct wlr_scene_tree *layers[] = { &trees[0], &trees[1], &trees[2] };
static struct wlr_scene_node *wlr_scene_node_at(struct wlr_scene_node *n,
        double x, double y, double *nx, double *ny) {
    (void)x; (void)y; (void)nx; (void)ny;
    return n->type ? n : NULL;
}
static struct wlr_scene_buffer *wlr_scene_buffer_from_node(struct wlr_scene_node *n) {
    return (struct wlr_scene_buffer *)n;
}
static struct wlr_scene_surface *wlr_scene_surface_try_from_buffer(struct wlr_scene_buffer *b) {
    return b->node.surface;
}
static void toplevel_from_wlr_surface(struct wlr_surface *s, Client **c, LayerSurface **l) {
    if (c) *c = s ? &s->client : NULL;
    if (l) *l = NULL;
}
'''
checks = r'''
int main(void) {
    struct wlr_surface client = { 42 }, *hit;
    struct wlr_scene_surface surface = { &client };
    Client *owner;
    trees[0].node = (struct wlr_scene_node){ 1, &surface };
    trees[1].node = (struct wlr_scene_node){ 1, NULL };
    xytonode(0, 0, &hit, &owner, NULL, NULL, NULL);
    assert(!hit && !owner); /* Rail blocks input to the client beneath it. */
    trees[1].node.surface = &surface;
    xytonode(0, 0, &hit, &owner, NULL, NULL, NULL);
    assert(hit == &client && owner == &client.client);
    trees[1].node.type = 0;
    xytonode(0, 0, &hit, &owner, NULL, NULL, NULL);
    assert(hit == &client);
    trees[0].node.type = 0;
    xytonode(0, 0, &hit, &owner, NULL, NULL, NULL);
    assert(!hit && !owner);
    xytonode(0, 0, NULL, NULL, NULL, NULL, NULL);
}
'''
with tempfile.TemporaryDirectory(prefix='nostromo-hit-test-') as directory:
    path = Path(directory)
    (path/'test.c').write_text(stubs+hit_test+checks)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(path/'test.c'),
                    '-o',str(path/'test')], check=True)
    subprocess.run([str(path/'test')], check=True)
print('dwl client/rail/empty hit tests passed.')
