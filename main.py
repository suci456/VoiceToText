"""
ParakeetAI Desktop Assistant
============================
Entry point for the ParakeetAI Desktop Assistant Windows application.
Launches the PySide6 modern dark-themed GUI desktop client.
"""

import os
import sys

# Ensure project root is in Python module search path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    """Main application lifecycle runner."""
    # Enable High DPI scaling & crisp font rendering
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ParakeetAI Desktop Assistant")
    app.setOrganizationName("ParakeetAI")
    app.setApplicationDisplayName("ParakeetAI Desktop Assistant")

    # Set Application Icon
    icon_path = os.path.join(PROJECT_ROOT, "assets", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

