"""Render the shipped start page with Qt WebEngine; no remote services opened."""
import json
import os
import tempfile
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
from pathlib import Path
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

root = Path(__file__).resolve().parents[2]
# The page loads its orb from beside its link, so render it where the home links it.
staged = tempfile.TemporaryDirectory(prefix="nostromo-start-")
home = Path(staged.name)
for line in (root / ".install/links.txt").read_text().splitlines():
    if line and not line.startswith("#"):
        source, destination = line.split("|")
        if destination.startswith(".local/share/nostromo/"):
            (home / destination).parent.mkdir(parents=True, exist_ok=True)
            (home / destination).symlink_to(root / source)
app = QApplication([])
for path in (root / "fonts").glob("*.ttf"):
    assert QFontDatabase.addApplicationFont(str(path)) >= 0
view = QWebEngineView()
view.resize(1080, 730)
view.show()
result = []

def capture():
    path = root / ".build/start-page.png"
    assert view.grab().save(str(path))
    result.append(path)
    app.quit()

def loaded(ok):
    assert ok, "Local start page failed to load"
    # Check the actual keyboard filter and retain placeholders until configured.
    # Qt returns a JavaScript array as an empty string, so the values travel as JSON.
    view.page().runJavaScript("JSON.stringify([document.querySelectorAll('[aria-disabled=true]').length,"
                             " document.querySelector('img.orb').naturalWidth])",
                             lambda values: result.append(json.loads(values)))
    QTimer.singleShot(1200, capture)

view.loadFinished.connect(loaded)
view.load(QUrl.fromLocalFile(str(home / ".local/share/nostromo/start/index.html")))
QTimer.singleShot(15000, app.quit)
app.exec()
staged.cleanup()
assert len(result) == 2 and result[0][0] == 6 and result[0][1] > 0, result
print("Actual local HTML rendered with Qt WebEngine; orb loaded, six service placeholders retained.")
