"""Render the shipped start page with Qt WebEngine; no remote services opened."""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
from pathlib import Path
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

root = Path(__file__).resolve().parents[1]
app = QApplication([])
for path in (root / "assets/fonts").glob("*.ttf"):
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
    view.page().runJavaScript("document.querySelectorAll('[aria-disabled=true]').length",
                             lambda count: result.append(count))
    QTimer.singleShot(1200, capture)

view.loadFinished.connect(loaded)
view.load(QUrl.fromLocalFile(str(root / "home/.local/share/nostromo/start/index.html")))
QTimer.singleShot(15000, app.quit)
app.exec()
assert len(result) == 2 and result[0] == 6, result
print("Actual local HTML rendered with Qt WebEngine; six service placeholders retained.")
