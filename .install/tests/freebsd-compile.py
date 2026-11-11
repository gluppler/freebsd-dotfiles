from pathlib import Path
import subprocess,shutil,hashlib,json

# Host-only check: cached FreeBSD headers and locally compiled scanner.
# Never runs a FreeBSD executable or installs packages on the host.
root=Path(__file__).resolve().parents[2];sysroot=root/'.build/freebsd-sysroot';usr=sysroot/'usr/local'
scanner=root/'.build/wayland-scanner';protocols=usr/'share/wayland-protocols'
base=root/'.build/downloads/freebsd-base.txz'
assert hashlib.sha256(base.read_bytes()).hexdigest() == '3768988b151c20f965679062b065c63a977d6bbb9f47fd83695ec2c40790c18f'
alphabet='ybndrfg8ejkmcpqxot1uwisza345h769'
for package in json.loads((root/'.install/tests/freebsd-headers.json').read_text()):
    archive=root/'.build/downloads'/('headers-'+package['name']+'.pkg')
    value=int.from_bytes(hashlib.blake2b(archive.read_bytes()).digest(),'little')
    assert package['sum']=='2$'+''.join(alphabet[(value >> i) & 31] for i in range(0,512,5)), package['name']

def run(args,cwd=None,**kw):
 subprocess.run([str(a) for a in args],cwd=cwd,check=True,**kw)
def copy(name,folder):
 p=root/'.build'/('cross-'+name)
 if p.exists():shutil.rmtree(p)
 shutil.copytree(folder,p)
 return p
def patch(p,path,level=1):
 with (root/path).open() as inp:run(['patch','-s','-F','0','-p'+str(level)],p,stdin=inp)
def scan(p,mode,path,name):run([scanner,mode,path,p/name])
flags=['cc','--target=x86_64-unknown-freebsd15.1','--sysroot='+str(sysroot),'-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fsyntax-only']
for folder in ['include','include/wlroots-0.20','include/pixman-1','include/cairo','include/pango-1.0','include/glib-2.0','lib/glib-2.0/include','include/harfbuzz','include/freetype2','include/libdrm','include/gtk-session-lock', 'include/gtk-session-lock-0', 'include/gtk-3.0','include/atk-1.0','include/at-spi-2.0','include/gdk-pixbuf-2.0','include/librsvg-2.0']:
 flags+=['-I'+str(usr/folder)]
p=copy('dwl',root/'.build/upstream/dwl')
patch(p,'dwl/clang.patch');patch(p,'dwl/nostromo.patch');patch(p,'dwl/ipc.patch');patch(p,'dwl/controls.patch');patch(p,'dwl/crt.patch');patch(p,'dwl/animation.patch')
for name in ['config.h','nostromo.h','ipc.h','crt.h','rail.h']:shutil.copy(root/'dwl'/name,p/name)
(p/'crt-shader.h').write_text(''.join(json.dumps(line+'\n')+'\n' for line in (root/'dwl/crt.frag').read_text().splitlines()))
for name,xml,mode in [('cursor-shape-v1','staging/cursor-shape/cursor-shape-v1.xml','enum-header'),('ext-image-copy-capture-v1','staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml','enum-header'),('pointer-constraints-unstable-v1','unstable/pointer-constraints/pointer-constraints-unstable-v1.xml','enum-header'),('xdg-shell','stable/xdg-shell/xdg-shell.xml','server-header')]:
 scan(p,mode,protocols/xml,name+'-protocol.h')
for name,mode in [('wlr-layer-shell-unstable-v1','enum-header'),('wlr-output-power-management-unstable-v1','server-header')]:scan(p,mode,p/'protocols'/(name+'.xml'),name+'-protocol.h')
scan(p,'server-header',root/'dwl/dwl-ipc-unstable-v2.xml','dwl-ipc-unstable-v2-protocol.h')
scan(p,'private-code',root/'dwl/dwl-ipc-unstable-v2.xml','dwl-ipc-unstable-v2-protocol.c')
scan(p,'server-header',root/'dwl/nostromo-control-v1.xml','nostromo-control-v1-server.h')
scan(p,'client-header',root/'dwl/nostromo-control-v1.xml','nostromo-control-v1-client.h')
scan(p,'private-code',root/'dwl/nostromo-control-v1.xml','nostromo-control-v1.c')
run(flags+['-DWLR_USE_UNSTABLE','-DVERSION="0.9-nostromo"','-I.','dwl.c','dwl-ipc-unstable-v2-protocol.c','nostromo-control-v1.c'],p)
run(flags+['-I'+str(p),root/'session/control.c',p/'nostromo-control-v1.c'])
scan(p,'client-header',protocols/'staging/ext-data-control/ext-data-control-v1.xml','ext-data-control-v1-client.h')
scan(p,'private-code',protocols/'staging/ext-data-control/ext-data-control-v1.xml','ext-data-control-v1.c')
run(flags+['-I'+str(p),root/'session/secret-copy.c',p/'ext-data-control-v1.c'])
print('FreeBSD dwl compile check passed')
p=copy('dwlb',next((root/'.build/upstream').glob('dwlb-*')))
patch(p,'dwlb/nostromo.patch');patch(p,'dwlb/scale.patch');patch(p,'dwlb/controls.patch');patch(p,'dwlb/reparse.patch');shutil.copy(root/'dwlb/config.h',p/'config.h')
for name,path in [('xdg-shell',protocols/'stable/xdg-shell/xdg-shell.xml'),('xdg-output-unstable-v1',protocols/'unstable/xdg-output/xdg-output-unstable-v1.xml'),('wlr-layer-shell-unstable-v1',p/'protocols/wlr-layer-shell-unstable-v1.xml'),('dwl-ipc-unstable-v2',p/'protocols/dwl-ipc-unstable-v2.xml')]:
 scan(p,'client-header',path,name+'-protocol.h');scan(p,'private-code',path,name+'-protocol.c')
run(flags+['-I.','dwlb.c']+list(p.glob('*-protocol.c')),p)
print('FreeBSD dwlb compile check passed')
p=copy('gtklock',root/'.build/upstream/gtklock-5.0.0')
patch(p,'gtklock/freebsd.patch',0);patch(p,'gtklock/nostromo.patch');patch(p,'gtklock/ack.patch')
shutil.copy(root/'gtklock/auth.c',p/'src/auth.c')
for name in ['theme.h','art.h']:shutil.copy(root/'gtklock'/name,p/'include'/name)
shutil.copy(root/'session/space-dots.h',p/'include/space-dots.h')
run(flags+['-Iinclude','-DGETTEXT_PACKAGE="gtklock"','-DLOCALEDIR="/usr/local/share/locale"','-DLIBDIR=/usr/local/lib','-DMAJOR_VERSION=5','-DMINOR_VERSION=0','-DMICRO_VERSION=0']+list((p/'src').glob('*.c')),p)
print('FreeBSD gtklock compile check passed')

p=copy('dvtm',root/'.build/upstream/dvtm-native')
shutil.copy(root/'dvtm/freebsd-cwd.h',p/'freebsd-cwd.h')
(p/'dvtm.c').write_bytes(subprocess.check_output(['sed','-f',str(root/'dvtm/freebsd.sed'),str(p/'dvtm.c')]))
(p/'vt.c').write_bytes(subprocess.check_output(['sed','/^static Row \\*buffer_row_last(/,/^}/d; /^static Row \\*buffer_row_prev(/,/^}/d',str(p/'vt.c')]))
for name in ('cwd','panes','editor'):patch(p,'dvtm/'+name+'.patch')
(p/'config.h').write_bytes(subprocess.check_output(['sed','-f',str(root/'dvtm/config.sed'),str(p/'config.def.h')]))
run(flags+['-D_XOPEN_SOURCE_EXTENDED','-DVERSION="0.15-nostromo"','-I.','dvtm.c','vt.c','dvtm-editor.c'],p)
print('FreeBSD dvtm compile check passed')

p=copy('nnn',root/'.build/upstream/nnn-5.3')
patch(p,'nnn/freebsd.patch')
run(flags+['-DNORL','-DDIM_FILTERED','src/nnn.c'],p)
print('FreeBSD nnn compile check passed')

p=copy('dunst',root/'.build/upstream/dunst-1.13.2')
patch(p,'dunst/nostromo.patch');patch(p,'dunst/freebsd.patch');shutil.copy(root/'dunst/nostromo.h',p/'src/nostromo.h')
for name,path in [('xdg-shell',protocols/'stable/xdg-shell/xdg-shell.xml'),('cursor-shape-v1',protocols/'staging/cursor-shape/cursor-shape-v1.xml'),('tablet-unstable-v2',protocols/'unstable/tablet/tablet-unstable-v2.xml'),('ext-idle-notify-v1',protocols/'staging/ext-idle-notify/ext-idle-notify-v1.xml')]+[(n,p/'src/wayland/protocols'/(n+'.xml')) for n in ('idle','wlr-foreign-toplevel-management-unstable-v1','wlr-layer-shell-unstable-v1')]:
 scan(p,'client-header',path,'src/wayland/protocols/'+name+'-client-header.h');scan(p,'private-code',path,'src/wayland/protocols/'+name+'.h')
run(flags+['-std=gnu11','-DENABLE_WAYLAND','-DHAVE_WL_CURSOR_SHAPE','-DHAVE_WL_EXT_IDLE_NOTIFY','-DVERSION="1.13.2-nostromo"','-DSYSCONFDIR="/usr/local/etc/xdg"']+list((p/'src').glob('*.c'))+list((p/'src/wayland').glob('*.c')),p)
print('FreeBSD Dunst Wayland compile check passed')

p=copy('fuzzel',root/'.build/upstream/fuzzel')
patch(p,'fuzzel/nostromo.patch');shutil.copy(root/'fuzzel/panel.h',p/'panel.h')
xml=['stable/xdg-shell/xdg-shell.xml','unstable/xdg-output/xdg-output-unstable-v1.xml','staging/xdg-activation/xdg-activation-v1.xml','staging/cursor-shape/cursor-shape-v1.xml','unstable/tablet/tablet-unstable-v2.xml','stable/viewporter/viewporter.xml','staging/fractional-scale/fractional-scale-v1.xml','unstable/primary-selection/primary-selection-unstable-v1.xml','staging/color-management/color-management-v1.xml','staging/single-pixel-buffer/single-pixel-buffer-v1.xml','unstable/text-input/text-input-unstable-v3.xml']
for path in [p/'external/wlr-layer-shell-unstable-v1.xml']+[protocols/i for i in xml]:
 name=path.stem;scan(p,'client-header',path,name+'.h');scan(p,'private-code',path,name+'.c')
run(['sh','generate-version.sh','1.15.0',p,p/'version.h'],p)
run(['python3','srgb.py',p/'srgb.c',p/'srgb.h'],p)
files='application char32 clipboard column config debug dmenu event fdm icon key-binding log main match path png prompt render shm uri wayland xdg xmalloc xsnprintf timing srgb'.split()
# Match upstream Meson's warning_level=1; our panel also has a separate -Wextra check.
run([f for f in flags if f != '-Wextra']+['-std=c18','-D_GNU_SOURCE','-I.','-I'+str(usr/'include/libepoll-shim')]+[n+'.c' for n in files]+[i.name for i in p.glob('*-v*.c')],p)
print('FreeBSD fuzzel compile check passed')

run(flags+['-I'+str(usr/'include/gtk-layer-shell'),root/'session/splash.c',root/'session/events.c'])
print('FreeBSD session event/splash compile checks passed')
run(flags+[root/'session/terminal-idle.c'])
print('FreeBSD terminal idle viewer compile check passed')
p=root/'.build/upstream/wireguard-tools-1.0.20260223/src'
run(flags+['-std=gnu99','-DRUNSTATEDIR="/var/run"','-I'+str(p/'uapi/freebsd')]+list(p.glob('*.c')))
print('FreeBSD wg-only compile check passed')

# Foot action/config changes compile against the same FreeBSD and Wayland APIs.
p=copy('foot',root/'.build/upstream/foot')
patch(p,'foot/nostromo.patch')
import re
for xml in re.findall(r"wayland_protocols_datadir / '([^']+)'", (p/'meson.build').read_text()):
 path=protocols/xml
 if path.exists(): scan(p,'client-header',path,path.stem+'.h')
run([f for f in flags if f != '-Wextra']+['-D_GNU_SOURCE','-DFOOT_DEFAULT_TERM="foot"','-DFOOT_GRAPHEME_CLUSTERING=1','-DHAVE_XDG_TOPLEVEL_TAG=1','-DHAVE_EXT_BACKGROUND_EFFECT=1','-I.','-I'+str(usr/'include/libepoll-shim'),'input.c','config.c','key-binding.c'],p)
print('FreeBSD foot action/config compile check passed')
