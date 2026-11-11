-- Swayimg 5.6: dwl owns the bottom rail; original image colours are preserved.
swayimg.appid = 'swayimg'
swayimg.decoration = true
swayimg.overlay = false
swayimg.fullscreen = false
swayimg.text.font = 'Michroma'
swayimg.text.size = 14
swayimg.text.color = 0xffffffff
swayimg.text.background = 0xff000000
swayimg.text.shadow = 0x00000000
swayimg.imagelist.adjacent = true

-- y copies the shown image to the Wayland clipboard. The path is single-quoted
-- for /bin/sh, so it is only an argument; & keeps the viewer responsive.
local function copy(view)
    local image = view.get_image()
    if image then
        os.execute("nostromo-clipboard image '" .. (image.path:gsub("'", "'\\''")) .. "' &")
    end
end

for _, view in ipairs({swayimg.viewer, swayimg.slideshow}) do
    view.default_scale = 'fit'
    view.default_position = 'center'
    view.preload = 1
    view.history = 1
    view.mark_color = 0xffffffff
    view.text = {bottomright = {'{list.index}/{list.total}  {scale}'}}
    view.set_window_background(0xff000000)
    view.set_image_background(0xff000000)
    view.on_key('q', function() swayimg.exit() end)
    view.on_key('n', function() view.open('next') end)
    view.on_key('p', function() view.open('prev') end)
    view.on_key('y', function() copy(view) end)
    for key, delta in pairs({h = {20, 0}, j = {0, -20}, k = {0, 20}, l = {-20, 0}}) do
        local x, y = delta[1], delta[2]
        view.on_key(key, function()
            local pos = view.get_position()
            view.set_abs_position(pos.x + x, pos.y + y)
        end)
    end
end

swayimg.gallery.window_color = 0xff000000
swayimg.gallery.unselected_color = 0xff000000
swayimg.gallery.selected_color = 0xff222222
swayimg.gallery.border_color = 0xffffffff
swayimg.gallery.border_size = 2
swayimg.gallery.hover = false
swayimg.gallery.preload = false
swayimg.gallery.cache = 24
swayimg.gallery.text = {bottomright = {'{list.index}/{list.total}'}}
swayimg.gallery.on_key('q', function() swayimg.exit() end)
swayimg.gallery.on_key('y', function() copy(swayimg.gallery) end)
for key, direction in pairs({h = 'left', j = 'down', k = 'up', l = 'right'}) do
    swayimg.gallery.on_key(key, function() swayimg.gallery.select(direction) end)
end

-- Update the Wayland title only when the displayed/selected filename changes.
-- The compositor uses this for the bottom extended bar; no second filename overlay.
local last_title
swayimg.on_redrawn(function()
    local view = swayimg[swayimg.mode]
    local image = view and view.get_image()
    local title = image and image.path:match('[^/]+$') or ''
    if title ~= last_title then
        swayimg.title = title
        last_title = title
    end
end)
