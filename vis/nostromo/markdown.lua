-- Live terminal layout from the unsaved buffer; no watcher, server or temp files.
local M = {}
local state, drawing
local limit = 128 * 1024

local function pause(message)
  state.paused = true
  vis:info(message .. ' Toggle Space mp to restart.')
end

local function update()
  if not state or drawing or state.paused then return end
  local s = state
  if s.source.file ~= s.file or s.preview.file ~= s.output then state = nil; return end
  if s.output.modified then pause('Preview was edited; changes kept.'); return end
  if s.file.size > limit then pause('Live preview is limited to 128 KiB.'); return end
  local width = math.max(12, s.preview.width - 2)
  local input = s.file:content(0, s.file.size)
  if input == s.input and width == s.width then return end
  -- vis:pipe itself redraws the UI. Guard that nested draw before spawning it.
  drawing = true
  local code, output, err = vis:pipe(s.file, {start = 0, finish = s.file.size},
    'lowdown -Tterm --term-no-ansi --term-hpadding=1 --term-columns=' .. width ..
    ' --term-width=' .. width)
  if code ~= 0 then
    drawing = nil
    pause('Markdown renderer failed: ' .. (err or tostring(code)))
    return
  end
  -- 3.1.1 emits plain text with --term-no-ansi. Strip overstrikes too for newer
  -- lowdown releases, which use backspace formatting with the same option.
  output = (output or ''):gsub('[^\n]\b', ''):gsub('[%z\1-\8\11-\31\127]', '')
  local old = s.output:content(0, s.output.size)
  if output ~= old then
    -- Only replace changed bytes; whole-buffer replacements grow undo history
    -- by a full rendered document on every keystroke.
    local first, last = 0, 0
    while first < math.min(#old, #output) and old:byte(first + 1) == output:byte(first + 1) do first = first + 1 end
    while last < math.min(#old, #output) - first and old:byte(#old - last) == output:byte(#output - last) do last = last + 1 end
    local pos = s.preview.selection.pos
    s.output:delete(first, #old - first - last)
    s.output:insert(first, output:sub(first + 1, #output - last))
    s.output.modified = false
    s.preview.selection.pos = math.min(pos, #output)
  end
  s.input, s.width = input, width
  vis:redraw()
  drawing = nil
end

function M.toggle()
  if state then
    local s = state
    if s.preview.file == s.output and s.output.modified then
      vis:info('Preview was edited; copy your changes or close it with :q! first.')
      return
    end
    state = nil
    if s.preview.file == s.output then s.preview:close(false) end
    return
  end
  if not require('nostromo/dashboard').leave(vis.win) then return end
  local source = vis.win
  if source.file.size > limit then vis:info('Live preview is limited to 128 KiB.'); return end
  if not vis:command('vnew') then return end
  local preview = vis.win
  for _, key in ipairs({'numbers', 'relativenumbers', 'cursorline', 'showeof'}) do preview.options[key] = false end
  preview:set_syntax(nil)
  state = {source = source, file = source.file, preview = preview, output = preview.file}
  vis.win = source
  update()
end

vis.events.subscribe(vis.events.UI_DRAW, update)
vis.events.subscribe(vis.events.WIN_CLOSE, function(win)
  if state and (win == state.source or win == state.preview) then state = nil end
end)
vis.events.subscribe(vis.events.FILE_SAVE_PRE, function(file)
  if state and file == state.output then
    vis:info('Generated preview: save the Markdown source instead.')
    return false
  end
end)
vis.events.subscribe(vis.events.WIN_STATUS, function(win)
  if state and win == state.preview then
    win:status(state.paused and ' MARKDOWN [paused]' or ' MARKDOWN', ' Space mp: close ')
    return true
  end
end)
return M
