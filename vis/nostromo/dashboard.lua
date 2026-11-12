-- The dashboard is an unnamed vis buffer; it never replaces an edited file.
local M = {windows = setmetatable({}, {__mode = 'k'})}
local clock, clock_name, pending, serial = nil, nil, '', 0

local function moving()
  local mode = os.getenv('NOSTROMO_EFFECTS')
  if not mode then
    local state = os.getenv('XDG_STATE_HOME') or (os.getenv('HOME') .. '/.local/state')
    local file = io.open(state .. '/nostromo/crt-mode')
    if file then mode = file:read('*l'); file:close() end
  end
  return not mode or mode == 'animated'
end

local function stop_clock()
  clock_name, pending = nil, ''
  -- vis:communicate returns a file handle; closing it sends the process SIGTERM.
  if clock then clock:close(); clock = nil end
end

local function columns(text)
  local _, n = text:gsub('[^\128-\191]', '')
  return n
end

function M.layout(width, height, art, entries)
  width, height = math.max(1,width), math.max(1,height-1)
  local menu, body, aw, mw = {}, {}, 0, 0
  for _,line in ipairs(art) do aw=math.max(aw,columns(line)) end
  for _,entry in ipairs(entries) do
    local line='['..entry.key..']  '..entry.label
    menu[#menu+1]=line; mw=math.max(mw,columns(line))
  end
  local span=mw
  if aw+6+mw<=width and math.max(#art,#menu)<=height then
    span=aw+6+mw
    local rows=math.max(#art,#menu)
    local ao,mo=math.floor((rows-#art)/2),math.floor((rows-#menu)/2)
    for row=1,rows do
      local left=art[row-ao] or ''
      body[row]=left..string.rep(' ',aw+6-columns(left))..(menu[row-mo] or '')
    end
  else
    if aw<=width and #art+1+#menu<=height then
      span=math.max(aw,mw)
      for _,line in ipairs(art) do body[#body+1]=string.rep(' ',math.floor((span-aw)/2))..line end
      body[#body+1]=''
    end
    for _,line in ipairs(menu) do body[#body+1]=string.rep(' ',math.max(0,math.floor((span-mw)/2)))..line:sub(1,width) end
  end
  local rows={}
  for _=1,math.max(0,math.floor((height-#body)/2)) do rows[#rows+1]='' end
  local pad=string.rep(' ',math.max(0,math.floor((width-span)/2)))
  for _,line in ipairs(body) do rows[#rows+1]=pad..line end
  return table.concat(rows,'\n')..'\n'
end

function M.leave(win)
  local state = M.windows[win]
  if not state then return true end
  if win.file == state.file and win.file.modified then
    vis:info('Dashboard was edited; save your changes to another buffer before continuing.')
    return false
  end
  for _, entry in ipairs(M.entries) do win:unmap(vis.modes.NORMAL, entry.key) end
  for key, value in pairs(state.options) do win.options[key] = value end
  if win.file == state.file then
    win.file:delete(0, win.file.size)
    win.file.modified = false
  end
  M.windows[win] = nil
  stop_clock()
  return true
end

local function draw(win)
  local state = M.windows[win]
  if not state then return end
  if win.file ~= state.file then M.leave(win); return end
  if win.file.modified or (state.width == win.width and state.height == win.height) then return end
  state.width, state.height = win.width, win.height
  local height = win.viewport and win.viewport.height or math.max(1,win.height-1)
  local pages, offsets, size = {}, {}, 0
  state.has_motion = false
  for _, art in ipairs(M.frames or {M.art}) do
    local page = M.layout(win.width, height+1, art, M.entries)
    local _, lines = page:gsub('\n', '')
    page = page .. string.rep('\n',math.max(0,height-lines))
    offsets[#offsets+1], size = size, size+#page
    if pages[1] and page ~= pages[1] then state.has_motion = true end
    pages[#pages+1] = page
  end
  -- Cache a bounded set of pages once. Animation never appends undo history.
  local content = table.concat(pages)
  state.offsets = offsets
  win.file:delete(0, win.file.size)
  win.file:insert(0, content)
  win.file.modified = false
  win.selection.pos = 0
end

function M.set_frame(index)
  local win = vis.win
  local state = M.windows[win]
  if not state or win.file ~= state.file or win.file.modified or
      vis.mode ~= vis.modes.NORMAL or (vis.input_queue or '') ~= '' then return end
  local offset = state.offsets[index+1]
  if not offset or offset == win.selection.pos then return end
  win.selection.pos = offset
  vis:feedkeys('zt')
  vis:redraw()
end

local function update_clock()
  local win = vis.win
  local state = M.windows[win]
  if not state or not state.has_motion or win.file ~= state.file or
      win.file.modified or vis.mode ~= vis.modes.NORMAL or not moving() then
    stop_clock()
    return
  end
  if not clock then
    serial = serial+1
    clock_name = 'nostromo-dashboard-' .. serial
    clock = vis:communicate(clock_name, 'nostromo-terminal-idle --ticks')
  end
end

function M.show()
  local win = vis.win
  if M.windows[win] then return end
  if win.file.name or win.file.size > 0 or win.file.modified then
    if not vis:command('open') then return end
    win = vis.win
  end
  local saved = {}
  for _, key in ipairs({'numbers', 'relativenumbers', 'cursorline', 'showeof'}) do
    saved[key] = win.options[key]
    win.options[key] = false
  end
  M.windows[win] = {file = win.file, options = saved}
  for _, entry in ipairs(M.entries) do
    win:map(vis.modes.NORMAL, entry.key, entry.action, entry.label)
  end
  draw(win)
  update_clock()
end

function M.new_file()
  local old = vis.win
  if not M.leave(old) then return end
  -- A fresh text object keeps generated dashboard text out of the new file's undo.
  if vis:command('new') then old:close(false) end
end

function M.setup(entries)
  M.entries, M.art = entries, {}
  local data = os.getenv('XDG_DATA_HOME') or (os.getenv('HOME') .. '/.local/share')
  local file = io.open(data .. '/nostromo/nostromo-orb-small.txt')
  if file then
    for line in file:lines() do M.art[#M.art + 1] = line end
    file:close()
  end
  M.frames = {}
  file = io.open(data .. '/nostromo/nostromo-orb-idle.txt')
  if file then
    local content = file:read(32768); file:close()
    for frame in (content .. '\f'):gmatch('(.-)\f') do
      local rows = {}
      for row in frame:gmatch('([^\n]*)\n') do rows[#rows+1] = row end
      if #rows > 0 then M.frames[#M.frames+1] = rows end
    end
  end
  if #M.frames ~= 4 then M.frames = {M.art} end
  vis.events.subscribe(vis.events.START, function()
    local count = 0
    for _ in vis:windows() do count = count + 1 end
    if count == 1 and not vis.win.file.name and vis.win.file.size == 0 and not vis.win.file.modified then M.show() end
  end)
  vis.events.subscribe(vis.events.UI_DRAW, function()
    for win in pairs(M.windows) do draw(win) end
    update_clock()
  end)
  vis.events.subscribe(vis.events.PROCESS_RESPONSE, function(name, kind, _, buffer)
    if name ~= clock_name then return end
    if kind == 'EXIT' or kind == 'SIGNAL' then clock = nil; clock_name = nil; return end
    if kind ~= 'STDOUT' then return end
    pending = pending .. buffer
    if #pending > 128 then stop_clock(); return end
    local last
    while true do
      local row, rest = pending:match('^([^\n]*)\n(.*)$')
      if not row then break end
      pending = rest
      if row:match('^[0-3]$') then last = tonumber(row) end
    end
    if last then M.set_frame(last) end
  end)
  vis.events.subscribe(vis.events.WIN_CLOSE, function(win)
    M.windows[win] = nil
    if not next(M.windows) then stop_clock() end
  end)
  vis.events.subscribe(vis.events.QUIT, stop_clock)
  vis.events.subscribe(vis.events.FILE_SAVE_PRE, function(file)
    for _, state in pairs(M.windows) do
      if file == state.file and not file.modified then vis:info('Use [n] for a new file.'); return false end
    end
  end)
end

return M
