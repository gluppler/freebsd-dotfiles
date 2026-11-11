/* ISC: Copyright 2026 Nostromo contributors. Provided without warranty. */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>
#include "nostromo-control-v1-client.h"
static struct nostromo_control_v1 *control;
static unsigned int effect,lock_state;
static int received;
static void state(void *data,struct nostromo_control_v1 *object,uint32_t mode,uint32_t locked) {
    effect=mode;lock_state=locked;received=1;
}
static const struct nostromo_control_v1_listener listener={.state=state};
static void global(void *data,struct wl_registry *registry,uint32_t name,const char *interface,uint32_t version) {
    if(strcmp(interface,nostromo_control_v1_interface.name))return;
    control=wl_registry_bind(registry,name,&nostromo_control_v1_interface,1);
    nostromo_control_v1_add_listener(control,&listener,NULL);
}
static void removed(void *data,struct wl_registry *registry,uint32_t name) {}
static const struct wl_registry_listener registry_listener={.global=global,.global_remove=removed};
int main(int argc,char **argv) {
    int wanted=-1;
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"off"))wanted=0;
    else if(!strcmp(argv[1],"static"))wanted=1;
    else if(!strcmp(argv[1],"animated"))wanted=2;
    else if(strcmp(argv[1],"status") && strcmp(argv[1],"is-locked"))return 2;
    alarm(3);
    struct wl_display *display=wl_display_connect(NULL);
    if(!display)return 1;
    struct wl_registry *registry=wl_display_get_registry(display);
    wl_registry_add_listener(registry,&registry_listener,NULL);
    if(wl_display_roundtrip(display)<0 || !control)return 1;
    if(wanted<0)nostromo_control_v1_get_state(control);
    else nostromo_control_v1_set_effect(control,(uint32_t)wanted);
    if(wl_display_roundtrip(display)<0 || !received || effect>2 || lock_state>2)return 1;
    nostromo_control_v1_destroy(control);wl_registry_destroy(registry);wl_display_disconnect(display);
    if(!strcmp(argv[1],"is-locked"))return lock_state==1?0:1;
    const char *modes[]={"off","static","animated"};
    printf("%s\n",modes[effect]);
    return wanted>=0 && effect!=(unsigned int)wanted?1:0;
}
