-- Execute the shipped configuration with only the viewer's host API substituted.
local redraw, shown, writes
writes = 0
local paths, keys = {}, {}
local function view(mode)
    keys[mode] = {}
    return {
        on_key = function(key, fn) keys[mode][key] = fn end,
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
dofile('swayimg/init.lua')
for _, mode in ipairs({'viewer', 'slideshow', 'gallery'}) do
    swayimg.mode = mode
    paths[mode] = '/home/alice/Pictures/' .. mode .. ' 日本語.png'
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

-- y hands the shown file to the clipboard helper. The real /bin/sh must see the
-- whole path, quotes and command syntax included, as one literal argument.
local executed
os.execute = function(command) executed = command; return true end
for _, mode in ipairs({'viewer', 'slideshow', 'gallery'}) do
    swayimg.mode = mode
    paths[mode] = "/home/alice/it's $(echo injected) `echo too` 日本語.png"
    keys[mode].y()
    local quoted = executed:match('^nostromo%-clipboard image (.+) &$')
    assert(quoted, executed)
    local shell = io.popen("printf '%s' " .. quoted)
    assert(shell:read('*a') == paths[mode], 'the shell must receive the path unchanged')
    shell:close()
    executed, paths[mode] = nil, nil
    keys[mode].y()
    assert(executed == nil, 'without an image nothing runs')
end
print('Swayimg y copies the shown image through the clipboard helper with a literal path.')
