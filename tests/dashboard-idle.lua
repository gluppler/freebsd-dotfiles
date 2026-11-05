-- The dashboard animates cached pages without modifying the text on each tick.
local handlers, writes, started, closed, keys = {}, 0, 0, 0, 0
local file = {text='', size=0, modified=false}
function file:delete() self.text=''; self.size=0; writes=writes+1 end
function file:insert(_, text) self.text=text; self.size=#text; writes=writes+1 end
local win = {file=file, width=108, height=34, viewport={height=33},
             options={}, selection={pos=0}}
function win:map() end
function win:unmap() end
vis = {win=win, modes={NORMAL=0, INSERT=1}, mode=0, input_queue='', events={}}
for _,name in ipairs({'START','UI_DRAW','WIN_CLOSE','FILE_SAVE_PRE','PROCESS_RESPONSE','QUIT'}) do
  vis.events[name]=name
end
function vis.events.subscribe(name, fn) handlers[name]=fn end
function vis:windows() local once=false; return function() if not once then once=true; return win end end end
function vis:communicate(name, command)
  assert(command=='nostromo-terminal-idle --ticks')
  started=started+1; self.process=name; return {}
end
function vis:close() closed=closed+1 end
function vis:feedkeys(value) assert(value=='zt'); keys=keys+1 end
function vis:redraw() end
function vis:info(message) self.message=message end

local dashboard=dofile('home/.config/vis/nostromo/dashboard.lua')
dashboard.setup({{key='n',label='New file',action=function() end}})
handlers.START()
assert(started==1 and file.size<32768 and not file.modified)
local content, count=file.text, writes
for i=1,1000 do dashboard.set_frame(i%4) end
assert(file.text==content and writes==count and keys>0)
local before=win.selection.pos
vis.input_queue='g'; dashboard.set_frame(2)
assert(win.selection.pos==before)
vis.input_queue=''
handlers.PROCESS_RESPONSE(vis.process,'STDOUT',0,'2')
assert(win.selection.pos==before)
handlers.PROCESS_RESPONSE(vis.process,'STDOUT',0,'\n')
assert(win.selection.pos==dashboard.windows[win].offsets[3] and writes==count)

file.modified=true; file.text=file.text..'personal edit'
handlers.UI_DRAW()
assert(closed==1 and started==1)
assert(not dashboard.leave(win) and file.text:match('personal edit$'))
file.modified=false; vis.mode=vis.modes.INSERT
handlers.UI_DRAW(); assert(started==1)
vis.mode=vis.modes.NORMAL
handlers.UI_DRAW(); assert(started==2)
win.width=20; win.height=12; win.viewport.height=11
handlers.UI_DRAW()
assert(not dashboard.windows[win].has_motion and closed==2)
handlers.QUIT()
assert(closed==2)
print('Dashboard pages remain bounded; partial ticks, pending keys, edits, small windows and shutdown pass')
