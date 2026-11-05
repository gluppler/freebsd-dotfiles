/* Taken from https://github.com/djpohly/dwl/issues/466 */
#define COLOR(hex)    { ((hex >> 24) & 0xFF) / 255.0f, \
                        ((hex >> 16) & 0xFF) / 255.0f, \
                        ((hex >> 8) & 0xFF) / 255.0f, \
                        (hex & 0xFF) / 255.0f }
/* appearance */
static const int sloppyfocus               = 0;  /* focus follows mouse */
static const int bypass_surface_visibility = 0;  /* 1 means idle inhibitors will disable idle tracking even if it's surface isn't visible  */
static const unsigned int borderpx         = 2;  /* border pixel of windows */
static const unsigned int snap             = 32; /* snap pixel */
static const float rootcolor[]             = COLOR(0x000000ff);
static const float bordercolor[]           = COLOR(0xffffffff);
static const float focuscolor[]            = COLOR(0xffffffff);
static const float urgentcolor[]           = COLOR(0xffffffff);
/* This conforms to the xdg-protocol. Set the alpha to zero to restore the old behavior */
static const float fullscreen_bg[]         = {0.0f, 0.0f, 0.0f, 1.0f}; /* You can also use glsl colors */

/* tagging - TAGCOUNT must be no greater than 31 */
#define TAGCOUNT (9)

/* logging */
static int log_level = WLR_ERROR;

static const Rule rules[] = {
    { NULL, NULL, 0, 1, -1 },
};

/* layout(s) */
static const Layout layouts[] = {
	/* symbol     arrange function */
	{ "[]=",      nostromo_tile },
	{ "><>",      NULL },    /* no layout function means floating behavior */
	{ "[M]",      monocle },
};

/* monitors */
/* (x=-1, y=-1) is reserved as an "autoconfigure" monitor position indicator
 * WARNING: negative values other than (-1, -1) cause problems with Xwayland clients due to
 * https://gitlab.freedesktop.org/xorg/xserver/-/issues/899 */
static const MonitorRule monrules[] = {
   /* name        mfact  nmaster scale layout       rotate/reflect                x    y
    * example of a HiDPI laptop monitor:
    { "eDP-1",    0.5f,  1,      2,    &layouts[0], WL_OUTPUT_TRANSFORM_NORMAL,   -1,  -1 }, */
	{ NULL,       0.65f, 1,      1,    &layouts[1], WL_OUTPUT_TRANSFORM_NORMAL,   -1,  -1 },
	/* default monitor rule: can be changed but cannot be eliminated; at least one monitor rule must exist */
};

/* keyboard */
static const struct xkb_rule_names xkb_rules = {
	/* can specify fields: rules, model, layout, variant, options */
	/* example:
	.options = "ctrl:nocaps",
	*/
	.layout = "us",
	.options = NULL,
};

static const int repeat_rate = 30;
static const int repeat_delay = 300;

/* Trackpad */
static const int tap_to_click = 1;
static const int tap_and_drag = 1;
static const int drag_lock = 0;
static const int natural_scrolling = 0;
static const int disable_while_typing = 1;
static const int left_handed = 0;
static const int middle_button_emulation = 0;
/* You can choose between:
LIBINPUT_CONFIG_SCROLL_NO_SCROLL
LIBINPUT_CONFIG_SCROLL_2FG
LIBINPUT_CONFIG_SCROLL_EDGE
LIBINPUT_CONFIG_SCROLL_ON_BUTTON_DOWN
*/
static const enum libinput_config_scroll_method scroll_method = LIBINPUT_CONFIG_SCROLL_2FG;

/* You can choose between:
LIBINPUT_CONFIG_CLICK_METHOD_NONE
LIBINPUT_CONFIG_CLICK_METHOD_BUTTON_AREAS
LIBINPUT_CONFIG_CLICK_METHOD_CLICKFINGER
*/
static const enum libinput_config_click_method click_method = LIBINPUT_CONFIG_CLICK_METHOD_BUTTON_AREAS;

/* You can choose between:
LIBINPUT_CONFIG_SEND_EVENTS_ENABLED
LIBINPUT_CONFIG_SEND_EVENTS_DISABLED
LIBINPUT_CONFIG_SEND_EVENTS_DISABLED_ON_EXTERNAL_MOUSE
*/
static const uint32_t send_events_mode = LIBINPUT_CONFIG_SEND_EVENTS_ENABLED;

/* You can choose between:
LIBINPUT_CONFIG_ACCEL_PROFILE_FLAT
LIBINPUT_CONFIG_ACCEL_PROFILE_ADAPTIVE
*/
static const enum libinput_config_accel_profile accel_profile = LIBINPUT_CONFIG_ACCEL_PROFILE_ADAPTIVE;
static const double accel_speed = 0.0;

/* You can choose between:
LIBINPUT_CONFIG_TAP_MAP_LRM -- 1/2/3 finger tap maps to left/right/middle
LIBINPUT_CONFIG_TAP_MAP_LMR -- 1/2/3 finger tap maps to left/middle/right
*/
static const enum libinput_config_tap_button_map button_map = LIBINPUT_CONFIG_TAP_MAP_LRM;

/* If you want to use the windows key for MODKEY, use WLR_MODIFIER_LOGO */
#define MODKEY WLR_MODIFIER_LOGO

#define TAGKEYS(KEY,TAG) \
	{ MODKEY,                    KEY,            view,            {.ui = 1 << TAG} }, \
	{ MODKEY|WLR_MODIFIER_CTRL,  KEY,            toggleview,      {.ui = 1 << TAG} }, \
	{ MODKEY|WLR_MODIFIER_SHIFT, KEY,            tag,             {.ui = 1 << TAG} }, \
	{ MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT,KEY,toggletag,  {.ui = 1 << TAG} }

/* helper for spawning shell commands in the pre dwm-5.0 fashion */
#define SHCMD(cmd) { .v = (const char*[]){ "/bin/sh", "-c", cmd, NULL } }

/* Commands are literal argv, never interpolated window titles or filenames. */
static const char *termcmd[] = { "foot", "--app-id=nostromo.foot", NULL };
static const char *menucmd[] = { "nostromo-launcher", NULL };
static const Key keys[] = {
    { MODKEY, XKB_KEY_Return, spawn, {.v = termcmd} },
    { MODKEY, XKB_KEY_space, spawn, {.v = menucmd} },
    { MODKEY, XKB_KEY_p, spawn, SHCMD("foot -e nostromo-project") },
    { MODKEY, XKB_KEY_b, spawn, SHCMD("nostromo-browser") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_e, spawn, SHCMD("foot -e nnn") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_n, spawn, SHCMD("foot -e vis") },
    { MODKEY, XKB_KEY_j, focusstack, {.i = +1} },
    { MODKEY, XKB_KEY_k, focusstack, {.i = -1} },
    { MODKEY, XKB_KEY_h, setmfact, {.f = -0.05f} },
    { MODKEY, XKB_KEY_l, setmfact, {.f = +0.05f} },
    { MODKEY, XKB_KEY_i, incnmaster, {.i = +1} },
    { MODKEY, XKB_KEY_d, incnmaster, {.i = -1} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_Return, zoom, {0} },
    { MODKEY, XKB_KEY_q, killclient, {0} },
    { MODKEY, XKB_KEY_w, nostromo_layout, {.v = &layouts[0]} },
    { MODKEY, XKB_KEY_e, nostromo_layout, {.v = &layouts[1]} },
    { MODKEY, XKB_KEY_r, nostromo_layout, {.v = &layouts[2]} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_r, togglefloating, {0} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_f, togglefullscreen, {0} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_l, spawn, SHCMD("nostromo-lock") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_q, spawn, SHCMD("nostromo-power logout") },
    { MODKEY, XKB_KEY_Tab, view, {0} },
    { MODKEY, XKB_KEY_comma, focusmon, {.i = WLR_DIRECTION_LEFT} },
    { MODKEY, XKB_KEY_period, focusmon, {.i = WLR_DIRECTION_RIGHT} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_comma, tagmon, {.i = WLR_DIRECTION_LEFT} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_period, tagmon, {.i = WLR_DIRECTION_RIGHT} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_h, nostromo_move, {.i = 0} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_j, nostromo_move, {.i = 1} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_k, nostromo_move, {.i = 2} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_l, nostromo_move, {.i = 3} },
    { MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT, XKB_KEY_h, nostromo_move, {.i = 4} },
    { MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT, XKB_KEY_j, nostromo_move, {.i = 5} },
    { MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT, XKB_KEY_k, nostromo_move, {.i = 6} },
    { MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT, XKB_KEY_l, nostromo_move, {.i = 7} },
    { MODKEY, XKB_KEY_F1, spawn, SHCMD("foot -e nostromo-welcome --keys") },
    { MODKEY, XKB_KEY_F2, spawn, SHCMD("nostromo-wifi") },
    { MODKEY, XKB_KEY_F3, spawn, SHCMD("nostromo-audio") },
    { MODKEY, XKB_KEY_F4, spawn, SHCMD("nostromo-display") },
    { MODKEY, XKB_KEY_F5, spawn, SHCMD("foot -e nostromo-software") },
    { MODKEY, XKB_KEY_F6, spawn, SHCMD("nostromo-vpn menu") },
    { MODKEY, XKB_KEY_F7, spawn, SHCMD("nostromo-crt toggle") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_space, spawn, SHCMD("nostromo-language next") },
    { 0, XKB_KEY_Print, spawn, SHCMD("nostromo-screenshot region") },
    { WLR_MODIFIER_SHIFT, XKB_KEY_Print, spawn, SHCMD("nostromo-screenshot full") },
    { 0, XKB_KEY_XF86AudioRaiseVolume, spawn, SHCMD("nostromo-audio up") },
    { 0, XKB_KEY_XF86AudioLowerVolume, spawn, SHCMD("nostromo-audio down") },
    { 0, XKB_KEY_XF86AudioMute, spawn, SHCMD("nostromo-audio mute") },
    { 0, XKB_KEY_XF86AudioMicMute, spawn, SHCMD("nostromo-audio mic") },
    { 0, XKB_KEY_XF86MonBrightnessUp, spawn, SHCMD("nostromo-brightness up") },
    { 0, XKB_KEY_XF86MonBrightnessDown, spawn, SHCMD("nostromo-brightness down") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_space, spawn, SHCMD("nostromo-menu") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_d, spawn, SHCMD("nostromo-browser --discord") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_j, nostromo_stack, {.i = +1} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_k, nostromo_stack, {.i = -1} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_w, spawn, SHCMD("nostromo-wifi") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_d, spawn, SHCMD("nostromo-display") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_p, spawn, SHCMD("nostromo-power") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_c, spawn, SHCMD("nostromo-clipboard") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_a, spawn, SHCMD("nostromo-audio") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_b, spawn, SHCMD("nostromo-bluetooth menu") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_c, spawn, SHCMD("nostromo-crt toggle") },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_s, nostromo_capture, {0} },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_s, spawn, SHCMD("nostromo-screenshot full") },
    { MODKEY, XKB_KEY_n, spawn, SHCMD("dunstctl close") },
    { MODKEY|WLR_MODIFIER_CTRL, XKB_KEY_n, spawn, SHCMD("dunstctl history-pop") },
    { MODKEY|WLR_MODIFIER_CTRL|WLR_MODIFIER_SHIFT, XKB_KEY_n, spawn, SHCMD("dunstctl set-paused toggle") },
    { MODKEY, XKB_KEY_g, spawn, SHCMD("dwlb -toggle-visibility all") },
    { MODKEY, XKB_KEY_apostrophe, nostromo_scratch, {0} },
    { MODKEY, XKB_KEY_minus, nostromo_gaps, {.i = -1} },
    { MODKEY, XKB_KEY_equal, nostromo_gaps, {.i = +1} },
    { MODKEY|WLR_MODIFIER_SHIFT, XKB_KEY_equal, nostromo_gaps, {.i = 0} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_h, nostromo_pointer, {.i = 0} },
    { MODKEY|WLR_MODIFIER_ALT|WLR_MODIFIER_SHIFT, XKB_KEY_h, nostromo_pointer, {.i = 10} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_j, nostromo_pointer, {.i = 1} },
    { MODKEY|WLR_MODIFIER_ALT|WLR_MODIFIER_SHIFT, XKB_KEY_j, nostromo_pointer, {.i = 11} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_k, nostromo_pointer, {.i = 2} },
    { MODKEY|WLR_MODIFIER_ALT|WLR_MODIFIER_SHIFT, XKB_KEY_k, nostromo_pointer, {.i = 12} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_l, nostromo_pointer, {.i = 3} },
    { MODKEY|WLR_MODIFIER_ALT|WLR_MODIFIER_SHIFT, XKB_KEY_l, nostromo_pointer, {.i = 13} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_Return, nostromo_pointer, {.i = 4} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_BackSpace, nostromo_pointer, {.i = 5} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_comma, nostromo_pointer, {.i = 6} },
    { MODKEY|WLR_MODIFIER_ALT, XKB_KEY_period, nostromo_pointer, {.i = 7} },
    TAGKEYS(XKB_KEY_1, 0), TAGKEYS(XKB_KEY_2, 1), TAGKEYS(XKB_KEY_3, 2),
    TAGKEYS(XKB_KEY_4, 3), TAGKEYS(XKB_KEY_5, 4), TAGKEYS(XKB_KEY_6, 5),
    TAGKEYS(XKB_KEY_7, 6), TAGKEYS(XKB_KEY_8, 7), TAGKEYS(XKB_KEY_9, 8),
#define CHVT(n) { WLR_MODIFIER_CTRL|WLR_MODIFIER_ALT, XKB_KEY_F##n, chvt, {.ui = n} }
    CHVT(1), CHVT(2), CHVT(3), CHVT(4), CHVT(5), CHVT(6),
    CHVT(7), CHVT(8), CHVT(9), CHVT(10), CHVT(11), CHVT(12),
};

static const Button buttons[] = {
	{ MODKEY, BTN_LEFT,   moveresize,     {.ui = CurMove} },
	{ MODKEY, BTN_MIDDLE, togglefloating, {0} },
	{ MODKEY, BTN_RIGHT,  moveresize,     {.ui = CurResize} },
};

static const Axis axes[] = {
	{ MODKEY, AxisUp,   spawn, SHCMD("nostromo-audio up") },
	{ MODKEY, AxisDown, spawn, SHCMD("nostromo-audio down") },
};
