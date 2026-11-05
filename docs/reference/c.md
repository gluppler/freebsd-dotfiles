# C: functions and callbacks

Read `man 3 strtol` for the conversion rules and error cases. This function
converts a complete decimal string, rejecting overflow and trailing characters.

```c
#include <errno.h>
#include <stdlib.h>

int parse_long(const char *text, long *result)
{
    char *end;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0')
        return -1;
    *result = value;
    return 0;
}
```

Both pointers must be valid. The caller owns the output storage. Check the return
value before using it.

A callback is a function pointer plus, often, a pointer to the caller's state:

```c
#include <stddef.h>

struct counter { unsigned value; };
typedef void (*event_fn)(void *context);

void count_event(void *context)
{
    struct counter *counter = context;
    ++counter->value;
}

void dispatch(event_fn callback, void *context)
{
    if (callback != NULL)
        callback(context);
}
```

Keep the context alive until the last callback. A callback invoked from an
interrupt or another thread has additional synchronization requirements.

Useful local pages: `man 3 malloc`, `man 3 free`, `man 3 memcpy`, `man 3 snprintf`,
`man 2 read`, `man 2 write`, and `man 1 clang`. Section 2 documents system calls;
section 3 documents library functions.
