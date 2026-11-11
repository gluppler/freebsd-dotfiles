"""Run the actual SDDM theme with Qt offscreen; never authenticates a real account."""
import os
import json
import subprocess
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_BACKEND"] = "software"
from pathlib import Path
from PySide6.QtCore import QUrl, Qt, QObject, Signal, Slot, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

root = Path(__file__).resolve().parents[2]
warnings = []
qInstallMessageHandler(lambda level, context, message: warnings.append(message))
app = QGuiApplication([])
assert QFontDatabase.addApplicationFont(str(root / "fonts/Michroma-Regular.ttf")) >= 0
app.setFont(QFont("Michroma"))

class Authentication(QObject):
    loginFailed = Signal()
    informationMessage = Signal(str)
    attempted = None

    @Slot(str, str, int)
    def login(self, user, password, session):
        self.attempted = (user, password, session)
        QTimer.singleShot(50, self.loginFailed.emit)

backend = Authentication()
view = QQuickView()
view.rootContext().setContextProperty("sddm", backend)
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.setSource(QUrl.fromLocalFile(str(root / "sddm/theme/Main.qml")))
assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
view.resize(1920, 1080)
view.show()
QTest.qWait(250)
item = view.rootObject()
login = item.findChild(QObject, "login")
password = item.findChild(QObject, "password")
assert login is not None and password is not None
assert item.property("effectMode") == "animated"
assert item.property("effectTime") > 0
item.setProperty("animateClock", False)
item.setProperty("effectTime", 1.5)
destination = root / ".build/previews"
destination.mkdir(parents=True, exist_ok=True)
for width, height in ((1920, 1080), (2560, 1440), (3840, 2160), (7680, 4320)):
    view.resize(width, height)
    QTest.qWait(150)
    capture = view.grabWindow()
    assert not capture.isNull()
    assert capture.save(str(destination / f"login-{width}x{height}.png"))
view.resize(1920, 1080)
item.setProperty("animateClock", True)
QTest.qWait(100)
for character in "alice": QTest.keyClick(view, character)
assert login.property("text") == "alice", login.property("text")
QTest.keyClick(view, Qt.Key_Tab)
for character in "preview-only": QTest.keyClick(view, character)
assert password.property("text") == "preview-only"
assert password.property("secret") is True
QTest.keyClick(view, Qt.Key_Return)
QTest.qWait(100)
assert backend.attempted == ("alice", "preview-only", 0)
assert password.property("text") == ""
assert item.property("busy") is False
assert item.property("errorText") == "Authentication failed"
# Static/off retain input geometry and stop the effect clock.
item.setProperty("animateClock", True)
for mode in ('static', 'off'):
    item.setProperty('effectMode', mode)
    before=item.property('effectTime')
    QTest.qWait(100)
    assert item.property('effectTime') == before
    assert password.property('secret') is True
item.setProperty('effectMode', 'animated')
item.setProperty('animateClock', False)
item.setProperty('errorText', '')
login.setProperty('text', '')
QTest.keyClick(view, Qt.Key_Backtab)
frames=root/'.build/native-preview/login'
frames.mkdir(parents=True,exist_ok=True)
view.resize(960,540)
for i in range(90):
    item.setProperty('effectTime',i/30)
    QTest.qWait(1)
    assert view.grabWindow().save(str(frames/f'{i:04}.png'))
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30',
    '-i',str(frames/'%04d.png'),'-frames:v','90','-filter_complex',
    '[0:v]format=rgb24,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer',
    '-loop','0',str(destination/'login.gif')],check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
    'stream=nb_frames,duration','-of','json',str(destination/'login.gif')],text=True))['streams'][0]
assert int(info['nb_frames'])==90 and abs(float(info['duration'])-3)<.04,info
assert not warnings, "\n".join(warnings)
print("Qt theme: four sizes and 3-second GIF rendered; focus, masking, dispatch, failed-login recovery and static/off passed.")
