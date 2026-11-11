local M = {}
local home = os.getenv('HOME')
local state = (os.getenv('XDG_STATE_HOME') or home .. '/.local/state') .. '/nostromo/vis'

function M.quote(s) return "'" .. s:gsub("'", "'\\''") .. "'" end

function M.choose(command, input)
  -- vis 0.9 accepts a File/Range, not a Lua string, as pipe input. Only
  -- generated filename lists go through this private temp; buffers never do.
  local temp
  if input and input ~= '' then
    local code, path = vis:pipe(nil, nil, 'umask 077; mktemp')
    if code ~= 0 or not path then vis:info('Could not stage picker choices.'); return end
    temp = path:gsub('\n$', '')
    local file, err = io.open(temp, 'w')
    if not file then os.remove(temp); vis:info(err); return end
    local written = file:write(input)
    local closed = file:close()
    if not written or not closed then os.remove(temp); vis:info('Could not write picker choices.'); return end
    command = command .. ' < ' .. M.quote(temp)
  end
  local ok, status, output, err = pcall(vis.pipe, vis, nil, nil, command, true)
  if temp then os.remove(temp) end
  if not ok then vis:info(tostring(status)); return end
  if status ~= 0 then
    if err and err ~= '' then vis:info(err) end
    return
  end
  return output and output:gsub('\n$', '')
end

function M.open(path, line, col, split)
  if not path or path == '' or path:find('[\r\n%z]') then return false end
  if not require('nostromo/dashboard').leave(vis.win) then return false end
  M.remember(vis.win)
  local escaped = path:gsub('([\\\t "\'])', '\\%1')
  if not vis:command((split or 'e') .. ' ' .. escaped) then return false end
  if line then vis.win.selection:to(tonumber(line), tonumber(col) or 1) end
  return true
end

function M.files(directory)
  local command = "rg --files --hidden -g '!.git'"
  if directory then command = 'cd ' .. M.quote(directory) .. ' && ' .. command .. ' | sed "s|^|./|"' end
  local path = M.choose(command .. " | fzf --prompt='FILE > '")
  if path and directory then path = directory .. '/' .. path end
  M.open(path)
end

function M.search()
  local result = M.choose("rg --line-number --no-heading --color=never . | fzf --delimiter=: --prompt='SEARCH > '")
  if not result then return end
  local path, line = result:match('^(.-):(%d+):')
  if path then M.open(path, line) end
end

local function read_rows(path)
  local rows, file = {}, io.open(path)
  if file then for line in file:lines() do rows[#rows + 1] = line end; file:close() end
  return rows
end

local function write_rows(path, rows)
  local command = 'umask 077; mkdir -p ' .. M.quote(state) .. ' || exit; ' ..
    'tmp=$(mktemp ' .. M.quote(state .. '/write.XXXXXXXX') .. ') || exit; ' ..
    'trap \'rm -f "$tmp"\' 0; cat > "$tmp" && mv "$tmp" ' .. M.quote(path)
  local pipe = io.popen(command, 'w')
  if not pipe then vis:info('Could not save editor state.'); return false end
  local written = pipe:write(table.concat(rows, '\n') .. '\n')
  local closed = pipe:close()
  if not written or not closed then vis:info('Could not save editor state.'); return false end
  return true
end

local function position(win)
  local path = win.file.path
  if not path or path:find('[\r\n\t]') then return end
  return path .. '\t' .. tostring(win.selection.line) .. '\t' .. tostring(win.selection.col)
end

function M.remember(win)
  local row = position(win)
  if not row then return end
  local rows = {row}
  for _, old in ipairs(read_rows(state .. '/recent')) do
    if #rows < 100 and old:match('^[^\t]+') ~= win.file.path then rows[#rows + 1] = old end
  end
  write_rows(state .. '/recent', rows)
end

local function pick_rows(path, prompt)
  local rows, choices = read_rows(path), {}
  for i, row in ipairs(rows) do choices[i] = row:match('^[^\t]+') end
  local picked = M.choose('fzf --prompt=' .. M.quote(prompt), table.concat(choices, '\n'))
  if not picked then return end
  for _, row in ipairs(rows) do
    local name, line, col = row:match('^(.-)\t(%d+)\t(%d+)$')
    if name == picked then M.open(name, line, col); return end
  end
end

function M.recent() pick_rows(state .. '/recent', 'RECENT > ') end
function M.bookmarks() pick_rows(state .. '/bookmarks', 'BOOKMARK > ') end
function M.bookmark_open(index)
  local row = read_rows(state .. '/bookmarks')[index]
  if row then
    local name, line, col = row:match('^(.-)\t(%d+)\t(%d+)$')
    M.open(name, line, col)
  end
end
function M.bookmark()
  local row = position(vis.win)
  if not row then vis:info('Save the file before bookmarking it.'); return end
  local rows = read_rows(state .. '/bookmarks')
  for i, old in ipairs(rows) do
    if old:match('^[^\t]+') == vis.win.file.path then rows[i] = row; write_rows(state .. '/bookmarks', rows); return end
  end
  rows[#rows + 1] = row
  write_rows(state .. '/bookmarks', rows)
end

function M.windows()
  local choices, windows = {}, {}
  for win in vis:windows() do
    windows[#windows + 1] = win
    choices[#choices + 1] = #windows .. '  ' .. (win.file.name or '[unnamed]')
  end
  local picked = M.choose("fzf --prompt='BUFFER > '", table.concat(choices, '\n'))
  local index = picked and tonumber(picked:match('^%d+'))
  if index and windows[index] then vis.win = windows[index] end
end

local function session_path()
  local code, output = vis:pipe(nil, nil, 'pwd -P | cksum')
  local id = code == 0 and output and output:match('^%d+')
  return id and state .. '/session-' .. id
end

function M.save_session()
  local path, rows = session_path(), {}
  if not path then return end
  for win in vis:windows() do
    if win.file.modified then vis:info('Save modified files before saving the session.'); return end
    local row = position(win)
    if row then rows[#rows + 1] = row end
  end
  if #rows > 0 then write_rows(path, rows) end
end

function M.restore_session()
  local path = session_path()
  if not path then return end
  for win in vis:windows() do
    if win.file.modified then vis:info('Save modified files before restoring a session.'); return end
  end
  local existing = {}
  for win in vis:windows() do if win.file.path then existing[win.file.path] = win end end
  for _, row in ipairs(read_rows(path)) do
    local name, line, col = row:match('^(.-)\t(%d+)\t(%d+)$')
    if name then
      local file = io.open(name)
      if file then
        file:close()
        if existing[name] then
          vis.win = existing[name]
          vis.win.selection:to(tonumber(line), tonumber(col))
        else
          -- Replacing a window invalidates its Lua reference. Keep existing
          -- files alive while adding missing session files, including the first.
          if not M.open(name, line, col, 'open') then return end
          existing[name] = vis.win
        end
      end
    end
  end
end

function M.help() vis:command('!nostromo-welcome --keys') end
return M
