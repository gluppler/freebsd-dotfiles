require('vis')
if os.getenv('NOSTROMO_COPY_MODE') == '1' then
  vis.events.subscribe(vis.events.INIT, function() vis:command('set theme nostromo') end)
  vis:map(vis.modes.NORMAL, 'q', ':q!<Enter>', 'Cancel copy')
  vis:map(vis.modes.VISUAL, 'y', ':wq!<Enter>', 'Copy selection')
  vis:map(vis.modes.VISUAL, '<Enter>', ':wq!<Enter>', 'Copy selection')
  return
end
local flow = require('nostromo/workflow')
local dashboard = require('nostromo/dashboard')
local lsp = require('nostromo/lsp')
local markdown = require('nostromo/markdown')

local function command(text) return function() vis:command(text) end end
local function task(action)
  return function()
    if not dashboard.leave(vis.win) then return end
    -- Build/test/lint may read other open files: refuse to use stale saved copies.
    local current = vis.win
    for win in vis:windows() do
      if win.file.modified then
        vis.win = win
        if not vis:command('w') then vis.win = current; return end
      end
    end
    vis.win = current
    local filename = current.file.path
    local needs_file = action == 'check' or action == 'test-file'
    if needs_file and not filename then vis:info('Save this file first.'); return end
    local suffix = needs_file and (' ' .. flow.quote(filename)) or ''
    vis:command('!nostromo-dev ' .. action .. suffix)
  end
end

local function format()
  local file = vis.win.file
  if not file.name then vis:info('Save this file before formatting.'); return end
  local input = file:content(0, file.size)
  local status, output, err = vis:pipe(file, {start = 0, finish = file.size},
    'nostromo-dev format ' .. flow.quote(file.name))
  if status ~= 0 or not output or (output == '' and input ~= '') then
    vis:info(err and err ~= '' and err or 'Formatter failed or returned empty output; buffer kept.')
    return
  end
  if output == input then return end
  local line, col = vis.win.selection.line, vis.win.selection.col
  file:snapshot()
  file:delete(0, file.size)
  file:insert(0, output)
  file:snapshot()
  vis.win.selection:to(line, col)
end

vis.events.subscribe(vis.events.INIT, function()
  vis:command('set theme nostromo')
  vis:command('set autoindent')
end)
vis.events.subscribe(vis.events.WIN_OPEN, function(win)
  win.options.numbers = true
  win.options.relativenumbers = true
  win.options.cursorline = true
  win.options.tabwidth = 4
  win.options.expandtab = win.syntax ~= 'go' and win.syntax ~= 'makefile'
  flow.remember(win)
end)
vis.events.subscribe(vis.events.WIN_CLOSE, flow.remember)
vis.events.subscribe(vis.events.FILE_SAVE_POST, function(file)
  if vis.win.file == file then flow.remember(vis.win) end
end)

local normal = vis.modes.NORMAL
local function map(keys, action, label)
  -- vis 0.9 requires a literal space; <Space> is not a recognized key name.
  vis:map(normal, keys:gsub('<Space>', ' '), action, label)
end
map('<Space><Space>', flow.files, 'Find project file')
map('<Space>ff', flow.files, 'Find project file')
map('<Space>fr', flow.recent, 'Recent files')
map('<Space>/', flow.search, 'Search project text')
map('<Space>gg', command('!lazygit'), 'Git')
map('<Space>e', command('!nnn'), 'File manager')
map('<Space>H', flow.bookmark, 'Bookmark file and position')
map('<Space>h', flow.bookmarks, 'Working files')
for i = 1, 9 do map('<Space>' .. i, function() flow.bookmark_open(i) end, 'Working file ' .. i) end
map('<Space>fb', flow.windows, 'Open buffers')
map('<Space>qs', flow.save_session, 'Save editor session')
map('<Space>qr', flow.restore_session, 'Restore editor session')
map('<Space>cf', format, 'Format buffer')
map('<Space>bb', task('build'), 'Build project')
map('<Space>tt', task('test'), 'Test project')
map('<Space>tT', task('test'), 'Test project')
map('<Space>tf', task('test-file'), 'Test Python file or Go package')
map('<Space>tr', task('test-pick'), 'Choose a discovered test')
map('<Space>tl', task('last'), 'Repeat last project task')
map('<Space>cl', task('check'), 'Lint current file')
map('<Space>cL', task('lint'), 'Lint project')
map('<Space>db', command('!nostromo-dev debug'), 'Native LLDB')
map('<Space>ch', command('!nostromo-dev health'), 'Development health')
map('<Space>od', command('!nostromo-docs menu'), 'Offline documentation')
map('<Space>sk', flow.help, 'Keybindings')
map('<Space>?', flow.help, 'Keybindings')
map('<Space>bh', dashboard.show, 'Orb dashboard')
map('<Space>mp', markdown.toggle, 'Toggle live Markdown preview')
map('<C-h>', '<C-w>h', 'Focus left')
map('<C-j>', '<C-w>j', 'Focus below')
map('<C-k>', '<C-w>k', 'Focus above')
map('<C-l>', '<C-w>l', 'Focus right')
map('<C-s>', command('w'), 'Save')
map('<Space>ww', command('w'), 'Save')
map('<Space>wd', command('q'), 'Close window')
map('<Space>wv', command('vsplit'), 'Vertical editor split')
map('<Space>ws', command('split'), 'Horizontal editor split')
map('gd', lsp.command('definition'), 'Definition')
map('gD', lsp.command('declaration'), 'Declaration')
map('gi', lsp.command('implementation'), 'Implementation')
map('gr', lsp.command('references'), 'References')
map('K', lsp.command('hover'), 'Documentation')
map('<C-]>', lsp.command('definition'), 'Definition')
map('<C-t>', lsp.command('back'), 'LSP jump back')
map('<Space>cr', lsp.rename, 'Rename symbol')
map('<Space>cs', lsp.command('navigate-symbols'), 'Document symbols')
map('<Space>cd', lsp.command('show-diagnostics'), 'Line diagnostics')
map('[d', lsp.command('prev-diagnostic'), 'Previous diagnostic')
map(']d', lsp.command('next-diagnostic'), 'Next diagnostic')
for _, mode in ipairs({normal, vis.modes.INSERT}) do
  vis:map(mode, '<C- >', lsp.command('completion'), 'LSP completion')
  vis:map(mode, '<C-x><C-o>', lsp.command('completion'), 'LSP completion')
end

dashboard.setup({
  {key = 'f', label = 'Find file', action = flow.files},
  {key = 'n', label = 'New file', action = dashboard.new_file},
  {key = 'r', label = 'Recent files', action = flow.recent},
  {key = 'h', label = 'Working files', action = flow.bookmarks},
  {key = 's', label = 'Search project', action = flow.search},
  {key = 'o', label = 'Restore session', action = flow.restore_session},
  {key = 'g', label = 'Git', action = command('!lazygit')},
  {key = '?', label = 'Keybindings', action = flow.help},
  {key = 'q', label = 'Quit', action = command('q')},
})

-- Only this user-owned file is executable configuration; recent/session files are data.
local local_config = os.getenv('HOME') .. '/.config/vis/local.lua'
local file = io.open(local_config)
if file then file:close(); dofile(local_config) end
