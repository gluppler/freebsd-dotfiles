/^static char \*getcwd_by_pid(Client \*c) {/,/^}/c\
static char *getcwd_by_pid(Client *c) {\
    return c ? nostromo_cwd(c->pid) : NULL;\
}
/^#include "vt.h"/a\
#include "freebsd-cwd.h"
# sysctl headers can declare socket send() and MAX/MIN before dvtm's definitions.
s/send(/vtsend(/g
/^#define MAX(/i\
#ifndef MAX
/^#define MAX(/a\
#endif
/^#define MIN(/i\
#ifndef MIN
/^#define MIN(/a\
#endif
