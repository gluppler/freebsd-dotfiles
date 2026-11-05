# Apply to the pinned upstream config.def.h before compilation.
# Keep .bg/.bg256 = -1 so panes and the bar inherit foot's background alpha.
s/{ send,/{ vtsend,/g
s/#define MOD  CTRL('g')/#define MOD  CTRL('b')/
s/#define SCROLL_HISTORY 500/#define SCROLL_HISTORY 10000/
s/#define BAR_AUTOHIDE    true/#define BAR_AUTOHIDE    false/
s/#define BAR_POS         BAR_TOP/#define BAR_POS         BAR_BOTTOM/
s/#define MFACT 0.5/#define MFACT 0.65/
s/#define ENABLE_MOUSE true/#define ENABLE_MOUSE false/
s/#define SELECTED_ATTR.*$/#define SELECTED_ATTR (COLOR(BLUE) | A_BOLD)/
s/#define TAG_SEL.*$/#define TAG_SEL (COLOR(BLUE) | A_REVERSE | A_BOLD)/
s/COLOR_BLUE/COLOR_WHITE/g
s/\.fg256 = 68/.fg256 = 15/g
# Replace the original actions instead of creating duplicate shortcuts.
/{ { MOD, '[hjklegdHLcC?]',/d
/static KeyBinding bindings\[\] = {/a\
    { { MOD, 'N', }, { focusnextnm, { NULL } } },\
    { { MOD, 'P', }, { focusprevnm, { NULL } } },\
    { { MOD, '[', }, { copymode, { "nostromo-copy-editor" } } },\
    { { MOD, ']', }, { paste, { NULL } } },\
    { { MOD, 'c', }, { create, { NULL, NULL, "$CWD" } } },\
    { { MOD, 'C', }, { create, { NULL } } },\
    { { MOD, '?', }, { create, { "nostromo-welcome --keys", "Keys" } } },\
    { { MOD, 'g', }, { create, { "lazygit", "Git", "$CWD" } } },\
    { { MOD, 'G', }, { setlayout, { "+++" } } },\
    { { MOD, 'e', }, { create, { "vis", "Editor", "$CWD" } } },\
    { { MOD, 'd', }, { create, { "nostromo-docs", "Docs", "$CWD" } } },\
    { { MOD, '|', }, { create, { NULL, NULL, "$CWD" } } },\
    { { MOD, '-', }, { create, { NULL, NULL, "$CWD" } } },\
    { { MOD, 'h', }, { focusleft, { NULL } } },\
    { { MOD, 'j', }, { focusdown, { NULL } } },\
    { { MOD, 'k', }, { focusup, { NULL } } },\
    { { MOD, 'l', }, { focusright, { NULL } } },\
    { { MOD, 'H', }, { setmfact, { "-0.05" } } },\
    { { MOD, 'L', }, { setmfact, { "+0.05" } } },\
    { { MOD, 'z', }, { setlayout, { "[ ]" } } },

