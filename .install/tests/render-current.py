"""Reproducible host previews. Requires Cairo/Pango, Lua, ffmpeg and Qt cache."""
from pathlib import Path
import json
import html
import os
import re
import shlex
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
work = root / ".build/native-preview"
work.mkdir(exist_ok=True)
cache=work/"cache"
cache.mkdir(exist_ok=True)
os.environ["XDG_CACHE_HOME"]=str(cache)
out = root / ".build/previews"
out.mkdir(parents=True, exist_ok=True)

def run(args, **kwargs):
    subprocess.run([str(x) for x in args], cwd=root, check=True, **kwargs)

# Use the patched bar painter verbatim, including its active-tag fill.
bar = (root / ".build/cross-dwlb/dwlb.c").read_text()
start = bar.index("static void\nnostromo_tag(")
end = bar.index("static int\ndraw_frame(", start)
macro = (root / "dwlb/config.h").read_text().split("// use ipc")[0]
(work / "preview-tag.h").write_text(macro + bar[start:end])
# Only remove the upstream type-header dependency; the painter is unmodified.
draw = (root / ".build/upstream/dunst-1.13.2/src/draw.h").read_text()
enum = re.search(r"enum corner_pos \{.*?\};", draw, re.S).group()
(work / "preview-notification.h").write_text(enum + "\n" +
    (root / "dunst/nostromo.h").read_text().replace('#include "draw.h"', ''))

# Run the dashboard's actual responsive Lua layout, using its configured entries.
entries = re.findall(r"\{key = '([^']+)', label = '([^']+)'", (root / "vis/visrc.lua").read_text())
lua = "local entries={" + ",".join("{key="+json.dumps(k)+",label="+json.dumps(v)+"}" for k,v in entries) + "}\n"
lua += "local art={} for line in io.lines('art/nostromo-orb-small.txt') do art[#art+1]=line end\n"
lua += "local m=dofile('vis/nostromo/dashboard.lua')\n"
lua += "io.write(m.layout(108,34,art,entries))\n"
with (root / ".build/dashboard-preview.txt").open("w") as dest:
    run(["lua", "-"], input=lua, text=True, stdout=dest)

flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs",
    "pangocairo", "pixman-1", "fontconfig"], text=True))
run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-I"+str(work), "-I"+str(root/"session"),
     root / ".install/tests/render-current.c", *flags, "-lm", "-o", work / "render"])
run(["python3", ".install/tests/network-menus.py"],env={**os.environ,"NOSTROMO_MENU_PREVIEWS":str(work)})
run(["python3", ".install/tests/offline-docs.py"],env={**os.environ,"NOSTROMO_DOCS_PREVIEW":str(work/"docs-menu.txt")})
lowdown=os.environ.get("LOWDOWN") or shutil.which("lowdown")
if not lowdown:
    raise SystemExit("Install host lowdown or set LOWDOWN to its executable for the reference preview.")
reference=subprocess.check_output([lowdown,"-Tterm","--term-no-colour","--term-hpadding=1",
    "--term-width=70",str(root/"docs/reference/c.md")],text=True)
# Translate the reader's monochrome SGR styles into Pango for the host composition.
parts=re.split(r"\x1b\[([0-9;]*)m", "\n".join(reference.splitlines()[:32]))
markup=[]; bold=False; underline=False
for i,part in enumerate(parts):
    if i%2:
        for number in (int(n or 0) for n in part.split(';')):
            if number==0: bold=underline=False
            elif number==1: bold=True
            elif number==4: underline=True
            elif number==22: bold=False
            elif number==24: underline=False
    else:
        markup.append('<span weight="'+('bold' if bold else 'normal')+'" underline="'+
            ('single' if underline else 'none')+'">'+html.escape(part)+'</span>')
(work/"reference-markup.txt").write_text(''.join(markup))
(work/"example.c").write_text(re.search(r"```c\n(.*?)\n```",(root/"docs/reference/c.md").read_text(),re.S)[1])
actions=subprocess.check_output(["sh",str(root/"bin/nostromo-menu"),"--list"],text=True)
(work/"main-menu.txt").write_text("NOSTROMO > \n"+actions)
(work/"short-menu.txt").write_text("SELECT > \nUP\nDOWN\n")
(work/"long-menu.txt").write_text("DISPLAYS > \nCONFIGURE EXTERNAL DISPLAY AND REFRESH RATE\nKEEP CURRENT ARRANGEMENT\nBACK\n")
for scene in ("desktop", "browser", "workspace", "menu", "multiplexer", "notification", "lock", "viewers", "wifi", "vpn", "bluetooth", "docs", "panel-docs"):
    run([work / "render", scene, out / (scene+"-1920x1080.png"), 1920, 1080, .25])
for w,h in ((2560,1440),(3840,2160),(7680,4320)):
    run([work / "render", "desktop", out / f"desktop-{w}x{h}.png", w,h,.25])
for w,h,scale in ((800,600,1),(1920,1080,1),(3840,2160,2),(7680,4320,4)):
    for scene in ("panel-short","panel-long","bluetooth"):
        run([work/"render",scene,out/f"{scene}-{w}x{h}.png",w,h,.25,scale])
for scene,count,rate,step in (("splash",72,30,1/30),("lock",90,30,1/30),("idle",180,12,.5)):
    frames=work/scene
    frames.mkdir(exist_ok=True)
    for i in range(count):
        run([work/"render",scene,frames/f"{i:04}.png",960,540,i*step])
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",rate,
         "-i",frames/"%04d.png","-frames:v",count,"-filter_complex",
         "[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer",
         "-loop",0,out/(scene+".gif")])
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "stream=nb_frames,duration","-of","json",str(out/(scene+".gif"))],text=True))["streams"][0]
    assert int(info["nb_frames"])==count, (scene,info)
    assert abs(float(info["duration"])-count/rate)<1/rate, (scene,info)
print("Current native drawing functions rendered. Idle GIF compresses 90 seconds into 15.")
