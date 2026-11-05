-- Execute the shipped configuration with only the viewer's host API substituted.
local redraw, shown, writes
writes = 0
local paths = {}
local function view(mode)
    return {
        on_key = function() end,
        set_window_background = function() end,
        set_image_background = function() end,
        get_image = function() return paths[mode] and {path = paths[mode]} end,
    }
end
swayimg = setmetatable({
    text = {}, imagelist = {},
    viewer = view('viewer'), slideshow = view('slideshow'), gallery = view('gallery'),
    on_redrawn = function(fn) redraw = fn end,
}, {__newindex = function(self, key, value)
    if key == 'title' then shown = value; writes = writes + 1 else rawset(self, key, value) end
end})
dofile('home/.config/swayimg/init.lua')
for _, mode in ipairs({'viewer', 'slideshow', 'gallery'}) do
    swayimg.mode = mode
    paths[mode] = '/home/gluppler/Pictures/' .. mode .. ' 日本語.png'
    redraw()
    assert(shown == mode .. ' 日本語.png')
    local before = writes
    redraw()
    assert(writes == before, 'unchanged redraw must not send another title')
    paths[mode] = nil
    redraw()
    assert(shown == '')
end
print('Swayimg viewer/slideshow/gallery filenames update the bottom legend without a redraw loop.')
