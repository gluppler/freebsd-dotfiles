# Zephyr: a GPIO loop

This application needs a board devicetree with a usable `led0` alias. Check the
board's wiring and LED polarity before building or flashing it.

```c
#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

static const struct gpio_dt_spec led =
    GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int main(void)
{
    if (!gpio_is_ready_dt(&led))
        return -ENODEV;
    int rc = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
    if (rc < 0)
        return rc;
    for (;;) {
        rc = gpio_pin_toggle_dt(&led);
        if (rc < 0)
            return rc;
        k_msleep(500);
    }
}
```

`GPIO_DT_SPEC_GET` gets the controller, pin and flags from devicetree.
`gpio_is_ready_dt` checks the controller. `k_msleep` yields the thread while it
waits; a busy loop would waste CPU time.

The initialized workspace keeps Zephyr's `doc/`, `include/`, `samples/` and board
sources locally. Use `rg gpio_pin_toggle_dt include/zephyr/drivers/gpio.h` inside
the Zephyr tree to find the exact API declaration and comments. The blinky sample
also contains its CMake and Kconfig settings. Read the local **EMBEDDED.md** for
the FreeBSD build, target and probe setup. Fetch the chosen west modules while
online before relying on offline builds.
