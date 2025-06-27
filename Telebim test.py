#!/usr/bin/env python3
import sys
import os
import subprocess
import random
import time
import signal

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap

from bs4 import BeautifulSoup

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(REPO_PATH, "slides")
OFFLINE_DIR = os.path.join(REPO_PATH, "offline_pages")

DISPLAY_TIME_MS = 1.5 * 1000
UPDATE_INTERVAL_S = 60 * 60 * 1000 # godzina na git-pull
IDLE_POLL_MS = 100

IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp")


class SlideshowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setTextFormat(Qt.RichText)
        self.setCentralWidget(self.label)
        self.showFullScreen()

        self.items = []
        self.current = 0
        self.last_pull = 0

        self.refresh_content()
        self.start_time = time.time()

    def refresh_content(self):
        imgs = []
        for d in (IMAGES_DIR, OFFLINE_DIR):
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.lower().endswith(IMG_EXTS):
                    imgs.append(os.path.join(d, f))

        pages = []
        if os.path.isdir(OFFLINE_DIR):
            for f in os.listdir(OFFLINE_DIR):
                if f.lower().endswith(".html"):
                    pages.append(os.path.join(OFFLINE_DIR, f))

        self.items = [("img", p) for p in imgs] + [("page", p) for p in pages]
        random.shuffle(self.items)
        self.current = 0
        print(f"[INFO] Loaded {len(imgs)} images and {len(pages)} HTML pages.")

    def show_next(self):
        # co godzinę git pull + refresh
        if time.time() - self.last_pull > UPDATE_INTERVAL_S:
            print("[INFO] Performing hourly git pull…")
            res = subprocess.run(
                ["git", "-C", REPO_PATH, "pull"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                print("[OK] git pull succeeded")
                self.refresh_content()
            else:
                print("[ERROR] git pull failed:", res.stderr)
            self.last_pull = time.time()

        # jeśli brak pozycji ‒ nic nie rób
        if not self.items:
            return

        # wyświetl kolejny slajd
        typ, path = self.items[self.current]
        if typ == "img":
            pix = QPixmap(path)
            self.label.setPixmap(pix.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self._display_page(path)

        # przygotuj indeks na następny slajd
        self.current += 1
        if self.current >= len(self.items):
            random.shuffle(self.items)
            self.current = 0

    def _display_page(self, html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if table:
                styled = (
                        "<div style='font-family:monospace; font-size:16px; "
                        "padding:20px; background:#222; color:#eee;'>"
                        + str(table) + "</div>"
                )
                self.label.setText(styled)
                self.label.setPixmap(QPixmap())  # usuń poprzedni obraz
            else:
                self.label.setText(
                    "<div style='color:#f55;'>"
                    "⚠️ Brak tabeli w HTML."
                    "</div>"
                )
                self.label.setPixmap(QPixmap())
        except Exception as e:
            self.label.setText(
                f"<div style='color:#f55;'>"
                f"⚠️ Błąd parsowania {os.path.basename(html_path)}:<br>{e}"
                "</div>"
            )
            self.label.setPixmap(QPixmap())

    def keyPressEvent(self, event):
        # Esc też kończy program
        if event.key() == Qt.Key_Escape:
            QApplication.quit()


def main():
    signal.signal(signal.SIGINT, lambda *args: QApplication.quit())

    app = QApplication(sys.argv)
    win = SlideshowWindow()

    timer = QTimer()
    timer.timeout.connect(win.show_next)
    timer.start(int(DISPLAY_TIME_MS))

    # 3) Krótki timer „idle”, by Qt co 100 ms wracał do pythona i łapał SIGINT
    idle = QTimer()
    idle.timeout.connect(lambda: None)
    idle.start(IDLE_POLL_MS)

    # Startujemy od razu
    win.show_next()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
