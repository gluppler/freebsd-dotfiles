/* Native output/devd notifications; executes fixed user-side actions. */
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

struct Output { struct Output *next; uint32_t name; struct wl_output *output; };
static struct Output *outputs;
static const char *pending;
static int64_t pending_at;
static int64_t resumed_until;
static int64_t milliseconds(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) < 0) exit(1);
    return (int64_t)now.tv_sec * 1000 + now.tv_nsec / 1000000;
}
static void queue_action(const char *action) {
    /* Output bursts must not overwrite a more recent lid transition. */
    if (!strcmp(action,"outputs") && pending && strcmp(pending,"outputs")) return;
    pending=action;
    pending_at=milliseconds()+200;
}
static void geometry(void *d, struct wl_output *o, int32_t x, int32_t y,
    int32_t w, int32_t h, int32_t subpixel, const char *make, const char *model, int32_t transform) {}
static void mode(void *d, struct wl_output *o, uint32_t f, int32_t w, int32_t h, int32_t refresh) {}
static void done(void *d, struct wl_output *o) { queue_action("outputs"); }
static void scale(void *d, struct wl_output *o, int32_t factor) {}
static const struct wl_output_listener listener = { .geometry=geometry, .mode=mode, .done=done, .scale=scale };
static void add(void *d, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version) {
    if (strcmp(interface, wl_output_interface.name) || version < 2) return;
    struct Output *o = calloc(1, sizeof *o);
    if (!o) exit(1);
    o->name=name; o->next=outputs; outputs=o;
    o->output=wl_registry_bind(registry, name, &wl_output_interface, 2);
    wl_output_add_listener(o->output, &listener, o);
}
static void remove_output(void *d, struct wl_registry *r, uint32_t name) {
    for (struct Output **p=&outputs; *p; p=&(*p)->next) {
        if ((*p)->name != name) continue;
        struct Output *old=*p; *p=old->next;
        wl_output_destroy(old->output); free(old);
        queue_action("outputs");
        break;
    }
}
static const struct wl_registry_listener registry_listener = { .global=add, .global_remove=remove_output };
static bool has(const char *event, const char *token) {
    size_t n=strlen(token);
    for (const char *p=event; (p=strstr(p,token)); p++) {
        if ((p==event || p[-1]==' ' || p[-1]=='!') &&
            (p[n]==' ' || p[n]=='\n' || !p[n])) return true;
    }
    return false;
}
static void device_event(const char *event) {
    if (has(event,"system=ACPI") && has(event,"subsystem=Lid")) {
        if (has(event,"notify=0x00")) queue_action("closed");
        if (has(event,"notify=0x01")) queue_action("open");
    } else if (has(event,"system=ACPI") && has(event,"subsystem=Resume")) {
        /* A wake-button notification must not immediately put us back to sleep. */
        resumed_until=milliseconds()+2000;
        if (pending && !strcmp(pending,"sleep")) pending=NULL;
    } else if (has(event,"system=ACPI") && has(event,"subsystem=Button") && has(event,"notify=0x01")) {
        if (milliseconds()>=resumed_until) queue_action("sleep");
    } else if (strstr(event,"ukbd") || strstr(event,"DRM")) queue_action("outputs");
}
static int connect_devd(void) {
    int fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);
    struct sockaddr_un address={.sun_len=sizeof address,.sun_family=AF_UNIX,
        .sun_path="/var/run/devd.seqpacket.pipe"};
    if (fd>=0 && connect(fd,(struct sockaddr *)&address,sizeof address)==0) return fd;
    if (fd>=0) close(fd);
    return -1;
}
int main(void) {
    struct wl_display *display=wl_display_connect(NULL);
    if (!display) return 1;
    struct wl_registry *registry=wl_display_get_registry(display);
    wl_registry_add_listener(registry,&registry_listener,NULL);
    if (wl_display_roundtrip(display)<0) return 1;
    int devd=-1, retry_delay=1000;
    int64_t retry_at=0;
    queue_action("outputs");
    pid_t child=0;
    for (;;) {
        int64_t now=milliseconds();
        if (devd<0 && now>=retry_at) {
            devd=connect_devd();
            if (devd<0) {
                if (retry_delay==1000) perror("devd unavailable; retrying");
                retry_at=now+retry_delay;
                if (retry_delay<30000) retry_delay=retry_delay>15000?30000:retry_delay*2;
            } else { retry_delay=1000; queue_action("outputs"); }
        }
        if (child) {
            int status;
            if (waitpid(child,&status,WNOHANG)==child) {
                if (!WIFEXITED(status) || WEXITSTATUS(status)) fprintf(stderr,"Output/lid action failed; inspect session.log\n");
                child=0;
            }
        }
        if (!child && pending && now>=pending_at) {
            child=fork();
            if (!child) {
                close(wl_display_get_fd(display));
                if (devd>=0) close(devd);
                execlp("nostromo-output-change","nostromo-output-change",pending,(char *)NULL);
                _exit(127);
            }
            if (child<0) { perror("fork"); return 1; }
            pending=NULL;
        }
        while (wl_display_prepare_read(display)!=0)
            if (wl_display_dispatch_pending(display)<0) return 1;
        int flushed=wl_display_flush(display);
        if (flushed<0 && errno!=EAGAIN) { wl_display_cancel_read(display); break; }
        struct pollfd fds[]={{.fd=wl_display_get_fd(display),.events=POLLIN|(flushed<0?POLLOUT:0)},
            {.fd=devd,.events=POLLIN}};
        /* A pending event while a child runs must never turn this into poll(0). */
        int timeout=child?250:-1;
        now=milliseconds();
        if (!child && pending) timeout=pending_at>now?(int)(pending_at-now):0;
        if (devd<0) {
            int remaining=retry_at>now?(int)(retry_at-now):0;
            if (timeout<0 || remaining<timeout) timeout=remaining;
        }
        int ready=poll(fds,2,timeout);
        if (ready<0 && errno!=EINTR) { wl_display_cancel_read(display); return 1; }
        if (ready>0 && (fds[0].revents&POLLIN)) {
            if (wl_display_read_events(display)<0) return 1;
            if (wl_display_dispatch_pending(display)<0) return 1;
        } else wl_display_cancel_read(display);
        if (fds[0].revents&(POLLHUP|POLLERR)) break;
        if (devd>=0 && (fds[1].revents&POLLIN)) {
            char event[8192]; ssize_t n=recv(devd,event,sizeof event-1,0);
            if (n>0) {
                event[n]=0;
                device_event(event);
            } else if (!n || (errno!=EAGAIN && errno!=EINTR)) {
                close(devd); devd=-1; retry_at=milliseconds()+1000;
                fprintf(stderr,"devd disconnected; reconnecting\n");
            }
        }
        if (devd>=0 && (fds[1].revents&(POLLHUP|POLLERR))) { close(devd); devd=-1; retry_at=milliseconds()+1000; }
    }
    if (child>0) kill(child,SIGTERM);
    if (devd>=0) close(devd);
    wl_registry_destroy(registry);
    wl_display_disconnect(display);
    return 0;
}
