import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from voice_role.config import AppConfig
from voice_role.ui.styles import get_stylesheet


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("VoiceRole")
    app.setApplicationDisplayName("VoiceRole - 智能录音角色识别")
    app.setOrganizationName("VoiceRole")

    config = AppConfig()
    app.setStyleSheet(get_stylesheet())

    from voice_role.ui.main_window import MainWindow
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())
