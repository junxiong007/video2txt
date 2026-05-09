from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from voice_role.constants import SUPPORTED_FORMATS
from voice_role.core.audio_extractor import get_media_duration


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _format_duration(seconds: float) -> str:
    if seconds <= 0:
        return ""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


class DropZone(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._file_path = ""
        self.setAcceptDrops(True)
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)

        # Icon label
        self.icon_label = QLabel("\U0001F3A4")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px; border: none; background: transparent;")
        layout.addWidget(self.icon_label)

        # Instruction text
        self.instruction = QLabel("拖放音频/视频文件到此处\n或点击下方按钮浏览文件")
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction.setWordWrap(True)
        self.instruction.setObjectName("subtitleLabel")
        layout.addWidget(self.instruction)

        # Separator
        sep = QLabel("──── 或者输入在线链接 ────")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setObjectName("subtitleLabel")
        layout.addWidget(sep)

        # URL input row
        url_row = QHBoxLayout()
        url_row.setSpacing(4)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴视频/音频网页链接...")
        self.url_input.returnPressed.connect(self._on_url_submitted)
        url_row.addWidget(self.url_input)

        self.url_paste_btn = QPushButton("粘贴")
        self.url_paste_btn.setToolTip("从剪贴板粘贴链接")
        self.url_paste_btn.setFixedWidth(48)
        self.url_paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(self.url_paste_btn)

        self.url_confirm_btn = QPushButton("确认")
        self.url_confirm_btn.setToolTip("确认并加载链接")
        self.url_confirm_btn.setFixedWidth(48)
        self.url_confirm_btn.clicked.connect(self._on_url_submitted)
        url_row.addWidget(self.url_confirm_btn)
        layout.addLayout(url_row)

        # Browse button
        self.browse_btn = QPushButton("\U0001F4C1  浏览文件")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)

        # File info (hidden until file loaded)
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setVisible(False)
        layout.addWidget(self.info_label)

        # Supported formats
        formats = QLabel("支持: MP3, WAV, M4A, MP4, MKV, AVI...")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats.setObjectName("subtitleLabel")
        formats.setStyleSheet("font-size: 10pt; padding-top: 4px;")
        layout.addWidget(formats)

        layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = url.toLocalFile()
            if any(path.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                event.acceptProposedAction()
                self.setStyleSheet(self._drag_style(True))
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._drag_style(False))

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._drag_style(False))
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            self._load_file(path)
            event.acceptProposedAction()

    def _browse(self):
        filter_str = "媒体文件 (" + " ".join(f"*{e}" for e in SUPPORTED_FORMATS) + ")"
        path, _ = QFileDialog.getOpenFileName(self, "选择音频或视频文件", "", filter_str)
        if path:
            self._load_file(path)

    def _is_url(self, text: str) -> bool:
        try:
            return urlparse(text).scheme in ("http", "https")
        except Exception:
            return False

    def _paste_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            self._on_url_submitted()

    def _on_url_submitted(self):
        text = self.url_input.text().strip()
        if not text:
            return
        if self._is_url(text):
            self.url_input.setStyleSheet("")
            self._file_path = text
            self.info_label.setText(f"\U0001F310 {text[:60]}{'...' if len(text) > 60 else ''}")
            self.info_label.setVisible(True)
            self.instruction.setText("已输入在线链接，点击右侧按钮重新输入")
            self.icon_label.setText("\U0001F30D")
            self.file_selected.emit(text)
        else:
            self.url_input.setStyleSheet(
                "border: 2px solid #C0392B; border-radius: 4px;"
            )

    def _load_file(self, path: str):
        import os
        self._file_path = path
        fname = os.path.basename(path)
        size = _format_size(os.path.getsize(path))
        try:
            dur = get_media_duration(path)
        except Exception:
            dur = 0

        info = f"\U0001F4C4 {fname}\n\U0001F4E6 {size}"
        if dur > 0:
            info += f"  |  ⏱ {_format_duration(dur)}"

        self.info_label.setText(info)
        self.info_label.setVisible(True)
        self.instruction.setText("点击下方按钮更换文件")
        self.icon_label.setText("✅")
        self.file_selected.emit(path)

    @property
    def file_path(self) -> str:
        return self._file_path

    def _drag_style(self, active: bool) -> str:
        from voice_role.ui.theme import COLORS
        if active:
            return (
                f"DropZone {{ border: 3px solid {COLORS['gold_primary']}; "
                f"border-radius: 12px; background-color: {COLORS['gold_pale']}; }}"
            )
        return (
            f"DropZone {{ border: 2px dashed {COLORS['gold_primary']}; "
            f"border-radius: 12px; background-color: {COLORS['bg_secondary']}; }}"
        )
