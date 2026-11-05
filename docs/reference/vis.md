# vis: a keybinding and a save hook

Put personal Lua configuration in `~/.config/vis/local.lua`. It is loaded after
the shared configuration.

```lua
vis:map(vis.modes.NORMAL, ' Z', function()
    vis.win.options.numbers = not vis.win.options.numbers
end, 'Toggle line numbers')

vis.events.subscribe(vis.events.FILE_SAVE_POST, function(file)
    if file.path then
        vis:info('Saved ' .. file.path)
    end
end)
```

The leading literal space makes the first binding **Space Z**. `FILE_SAVE_POST`
runs after the save, so it can report success. Do not call `write` from a save
hook unless you guard against triggering the same hook again.

For documentation while editing, **Space od** opens the DOCS menu. In dvtm,
**Ctrl+B d** creates a documentation pane; **Ctrl+B h/j/k/l** moves between it and
the editor. `man vis` covers editing commands. The installed vis source/API
documentation is the reference for Lua events; Neovim plugin APIs do not apply.
