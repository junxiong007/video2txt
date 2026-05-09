from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFileDialog, QApplication,
)
from PyQt6.QtCore import pyqtSignal

from voice_role.models.segment import TranscriptionSegment
from voice_role.core.exporter import export_srt, export_vtt, export_txt, format_transcript


class ExportPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._segments: list[TranscriptionSegment] = []
        self._base_name = "output"
        self._setup()

    def _setup(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addStretch()

        self.btn_srt = QPushButton("导出 SRT")
        self.btn_srt.clicked.connect(lambda: self._export("srt"))
        self.btn_srt.setEnabled(False)
        layout.addWidget(self.btn_srt)

        self.btn_vtt = QPushButton("导出 VTT")
        self.btn_vtt.clicked.connect(lambda: self._export("vtt"))
        self.btn_vtt.setEnabled(False)
        layout.addWidget(self.btn_vtt)

        self.btn_txt = QPushButton("导出 TXT")
        self.btn_txt.clicked.connect(lambda: self._export("txt"))
        self.btn_txt.setEnabled(False)
        layout.addWidget(self.btn_txt)

        self.btn_copy = QPushButton("\U0001F4CB 复制全部")
        self.btn_copy.clicked.connect(self._copy_all)
        self.btn_copy.setEnabled(False)
        layout.addWidget(self.btn_copy)

        layout.addStretch()

    def set_segments(self, segments: list[TranscriptionSegment], base_name: str = "output"):
        self._segments = segments
        self._base_name = base_name
        has_data = bool(segments)
        self.btn_srt.setEnabled(has_data)
        self.btn_vtt.setEnabled(has_data)
        self.btn_txt.setEnabled(has_data)
        self.btn_copy.setEnabled(has_data)

    def _export(self, fmt: str):
        if not self._segments:
            return
        ext_map = {"srt": "SRT 文件 (*.srt)", "vtt": "VTT 文件 (*.vtt)", "txt": "TXT 文件 (*.txt)"}
        path, _ = QFileDialog.getSaveFileName(
            self, f"导出 {fmt.upper()}", f"{self._base_name}.{fmt}", ext_map.get(fmt, "")
        )
        if not path:
            return
        if fmt == "srt":
            export_srt(self._segments, path)
        elif fmt == "vtt":
            export_vtt(self._segments, path)
        else:
            export_txt(self._segments, path)

    def _copy_all(self):
        if not self._segments:
            return
        text = format_transcript(self._segments)
        QApplication.clipboard().setText(text)
