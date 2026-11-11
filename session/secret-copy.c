/* ISC: Copyright 2026 Nostromo contributors. Provided without warranty.
 * Bounded, memory-only password clipboard. Destruction releases ONLY our source;
 * it never sends set_selection(NULL), which could erase a later selection. */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>
#include <wayland-client.h>
#include "ext-data-control-v1-client.h"

#define LIMIT (1024 * 1024)
static unsigned char secret[LIMIT + 1];
static size_t length;
static int finished, primary_available;
static struct wl_seat *seat;
static struct ext_data_control_manager_v1 *manager;

static void cancelled(void *data, struct ext_data_control_source_v1 *source) { finished=1; }
static void send_secret(void *data, struct ext_data_control_source_v1 *source, const char *mime, int32_t fd) {
    /* Never return the password for the sensitivity hint or an unoffered MIME. */
    if (!strcmp(mime,"text/plain;charset=utf-8") || !strcmp(mime,"text/plain")) {
        size_t offset=0;
        while (offset<length) {
            ssize_t n=write(fd,secret+offset,length-offset);
            if(n>0)offset+=(size_t)n;
            else if(n<0 && errno==EINTR)continue;
            else break;
        }
    }
    close(fd);
}
static const struct ext_data_control_source_v1_listener source_listener={.send=send_secret,.cancelled=cancelled};
static void offer_mime(void *data, struct ext_data_control_offer_v1 *offer, const char *mime) {}
static const struct ext_data_control_offer_v1_listener offer_listener={.offer=offer_mime};
static void offer_new(void *data, struct ext_data_control_device_v1 *device, struct ext_data_control_offer_v1 *offer) {
    ext_data_control_offer_v1_add_listener(offer,&offer_listener,NULL);
}
static void selection(void *data, struct ext_data_control_device_v1 *device, struct ext_data_control_offer_v1 *offer) {
    if(offer)ext_data_control_offer_v1_destroy(offer);
}
static void primary(void *data, struct ext_data_control_device_v1 *device, struct ext_data_control_offer_v1 *offer) {
    primary_available=1;selection(data,device,offer);
}
static void device_finished(void *data, struct ext_data_control_device_v1 *device) { finished=1; }
static const struct ext_data_control_device_v1_listener device_listener={
    .data_offer=offer_new,.selection=selection,.primary_selection=primary,.finished=device_finished
};
static void seat_capabilities(void *data, struct wl_seat *object, uint32_t capabilities) {}
static const struct wl_seat_listener seat_listener={.capabilities=seat_capabilities};
static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version) {
    if(!manager && !strcmp(interface,ext_data_control_manager_v1_interface.name))
        manager=wl_registry_bind(registry,name,&ext_data_control_manager_v1_interface,1);
    if(!seat && !strcmp(interface,wl_seat_interface.name)) {
        seat=wl_registry_bind(registry,name,&wl_seat_interface,1);
        wl_seat_add_listener(seat,&seat_listener,NULL);
    }
}
static void removed(void *data, struct wl_registry *registry, uint32_t name) {}
static const struct wl_registry_listener registry_listener={.global=global,.global_remove=removed};

int main(int argc, char **argv) {
    char *end;
    if(argc!=3 || (strcmp(argv[2],"clipboard") && strcmp(argv[2],"primary")))return 2;
    errno=0;
    unsigned long seconds=strtoul(argv[1],&end,10);
    if(errno || *end || !*argv[1] || seconds<1 || seconds>3600)return 2;
    struct rlimit core={0,0};
    if(setrlimit(RLIMIT_CORE,&core)<0)return 1;
    signal(SIGPIPE,SIG_IGN);
    alarm(5); /* Bound input and compositor startup as well as the expiry below. */
    (void)mlock(secret,sizeof secret);
    while(length<sizeof secret) {
        ssize_t n=read(STDIN_FILENO,secret+length,sizeof secret-length);
        if(n>0)length+=(size_t)n;
        else if(n==0)break;
        else if(errno!=EINTR)goto fail;
    }
    if(length>LIMIT)goto fail;
    struct wl_display *display=wl_display_connect(NULL);
    if(!display)goto fail;
    struct wl_registry *registry=wl_display_get_registry(display);
    wl_registry_add_listener(registry,&registry_listener,NULL);
    if(wl_display_roundtrip(display)<0 || !manager || !seat)goto disconnect;
    struct ext_data_control_device_v1 *device=ext_data_control_manager_v1_get_data_device(manager,seat);
    ext_data_control_device_v1_add_listener(device,&device_listener,NULL);
    if(wl_display_roundtrip(display)<0 || finished || (!strcmp(argv[2],"primary") && !primary_available))goto disconnect;
    struct ext_data_control_source_v1 *source=ext_data_control_manager_v1_create_data_source(manager);
    ext_data_control_source_v1_add_listener(source,&source_listener,NULL);
    ext_data_control_source_v1_offer(source,"text/plain;charset=utf-8");
    ext_data_control_source_v1_offer(source,"text/plain");
    ext_data_control_source_v1_offer(source,"x-kde-passwordManagerHint");
    if(!strcmp(argv[2],"primary"))ext_data_control_device_v1_set_primary_selection(device,source);
    else ext_data_control_device_v1_set_selection(device,source);
    if(wl_display_roundtrip(display)<0 || finished)goto disconnect;
    /* Only acknowledge after the compositor has processed our selection. */
    pid_t pid=fork();
    if(pid<0)goto disconnect;
    if(pid>0) {
        explicit_bzero(secret,sizeof secret);
        /* Do not destroy the child-owned Wayland objects or flush its socket. */
        _exit(0);
    }
    /* Memory locks are not inherited across fork. Best effort within the
     * account's native memlock limit; only lock the pages containing the secret. */
    (void)mlock(secret,length);
    if(setsid()<0)goto disconnect;
    signal(SIGHUP,SIG_IGN);
    int null=open("/dev/null",O_RDWR);
    if(null<0)goto disconnect;
    for(int fd=0;fd<3;fd++)if(dup2(null,fd)<0)goto disconnect;
    if(null>2)close(null);
    alarm((unsigned int)seconds); /* Also bounds a client that stops reading a paste. */
    while(!finished && wl_display_dispatch(display)>=0) {}
    explicit_bzero(secret,sizeof secret);
    wl_display_disconnect(display);
    return 0;
disconnect:
    wl_display_disconnect(display);
fail:
    explicit_bzero(secret,sizeof secret);
    fputs("Could not own the Wayland password clipboard.\n",stderr);
    return 1;
}
