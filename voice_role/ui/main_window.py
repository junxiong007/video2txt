from pathlib import Path
from urllib.parse import urlparse
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QAction

from voice_role.config import AppConfig
from voice_role.constants import PipelineState
from voice_role.models.segment import TranscriptionSegment
from voice_role.ui.theme import COLORS
from voice_role.ui.drop_zone import DropZone
from voice_role.ui.progress_panel import ProgressPanel
from voice_role.ui.subtitle_preview import SubtitleTable
from voice_role.ui.export_panel import ExportPanel
from voice_role.ui.settings_dialog import SettingsDialog
from voice_role.workers.signals import PipelineSignals
from voice_role.workers.pipeline_worker import PipelineWorker


def _is_url(path: str) -> bool:
    try:
        return urlparse(path).scheme in ("http", "https")
    except Exception:
        return False


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._pipeline_state = PipelineState.IDLE
        self._segments: list[TranscriptionSegment] = []
        self._input_path = ""
        self._worker: PipelineWorker | None = None
        self._worker_thread: QThread | None = None

        self.setWindowTitle("VoiceRole - 智能录音角色识别")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)

        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        open_action = QAction("打开文件...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("工具(&T)")
        settings_action = QAction("设置...", self)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # Title
        title = QLabel("VoiceRole")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("自动区分录音角色 · 智能字幕生成")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)
        root.addSpacing(4)

        # Main splitter: left drop zone + right subtitle table
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self._on_file_selected)
        splitter.addWidget(self.drop_zone)

        self.subtitle_table = SubtitleTable()
        splitter.addWidget(self.subtitle_table)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        # Progress panel
        self.progress_panel = ProgressPanel()
        root.addWidget(self.progress_panel)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_start = QPushButton("▶  开始处理")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self._on_start)
        self.btn_start.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("⏹  取消")
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_settings = QPushButton("⚙  设置")
        self.btn_settings.clicked.connect(self._on_settings)
        self.btn_settings.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_settings)

        root.addLayout(btn_layout)

        # Export panel
        self.export_panel = ExportPanel()
        root.addWidget(self.export_panel)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 — 请选择音频或视频文件")

    # ---- Slots ----

    def _on_file_selected(self, path: str):
        self._input_path = path
        self._segments = []
        self.subtitle_table.setRowCount(0)
        self.export_panel.set_segments([])
        self.progress_panel.reset()
        self._set_state(PipelineState.IDLE)
        if _is_url(path):
            display = path if len(path) <= 80 else path[:77] + "..."
            self.status_bar.showMessage(f"已输入链接: {display} — 点击「开始处理」下载并识别")
        else:
            fname = Path(path).name
            self.status_bar.showMessage(f"已选择: {fname} — 点击「开始处理」")

    def _on_open_file(self):
        from PyQt6.QtWidgets import QFileDialog
        from voice_role.constants import SUPPORTED_FORMATS
        filter_str = "媒体文件 (" + " ".join(f"*{e}" for e in SUPPORTED_FORMATS) + ")"
        path, _ = QFileDialog.getOpenFileName(self, "选择音频或视频文件", "", filter_str)
        if path:
            self.drop_zone._load_file(path)

    def _on_settings(self):
        dlg = SettingsDialog(self.config)
        dlg.exec()

    def _on_start(self):
        if not self._input_path:
            QMessageBox.warning(self, "提示", "请先选择音频/视频文件，或输入在线链接。")
            return

        if _is_url(self._input_path):
            self._set_state(PipelineState.DOWNLOADING)
        else:
            self._set_state(PipelineState.EXTRACTING)
        self.progress_panel.reset()
        self.subtitle_table.setRowCount(0)
        self.export_panel.set_segments([])
        self.status_bar.showMessage("正在处理...")

        # Worker setup
        self._worker_thread = QThread()
        self._worker = PipelineWorker(
            self.config, self._input_path,
            is_url=_is_url(self._input_path),
        )
        self._worker.moveToThread(self._worker_thread)

        signals = self._worker.signals
        signals.state_changed.connect(self._on_state_changed)
        signals.progress.connect(self._on_progress)
        signals.finished.connect(self._on_finished)
        signals.error_occurred.connect(self._on_error)

        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    def _on_cancel(self):
        if self._worker:
            self._worker.cancel()
        self.status_bar.showMessage("正在取消...")

    def _on_state_changed(self, state: PipelineState):
        self._pipeline_state = state
        self.progress_panel.set_state(state)

        is_running = state not in (
            PipelineState.IDLE, PipelineState.COMPLETE,
            PipelineState.ERROR, PipelineState.CANCELLED
        )
        self.btn_start.setEnabled(not is_running)
        self.btn_cancel.setEnabled(is_running)
        self.drop_zone.setEnabled(not is_running)

        if state == PipelineState.COMPLETE:
            self.status_bar.showMessage(
                f"处理完成 — 共 {len(self._segments)} 条字幕，{self._speaker_count()} 个说话人"
            )
            self.btn_start.setText("▶  开始处理")
        elif state == PipelineState.ERROR:
            self.status_bar.showMessage("处理出错")
            self.btn_start.setText("▶  开始处理")
        elif state == PipelineState.CANCELLED:
            self.status_bar.showMessage("已取消")
            self.btn_start.setText("▶  开始处理")

    def _on_progress(self, percent: int, message: str):
        self.progress_panel.set_progress(percent, message)

    def _on_finished(self, segments: list):
        self._segments = segments
        self.subtitle_table.load_segments(segments)
        if _is_url(self._input_path):
            base_name = "online_audio"
        else:
            base_name = Path(self._input_path).stem
        self.export_panel.set_segments(segments, base_name)
        self._set_state(PipelineState.COMPLETE)
        self._cleanup_worker()

    def _on_error(self, error_msg: str):
        self._set_state(PipelineState.ERROR)
        self.progress_panel.set_progress(0, f"错误: {error_msg}")
        QMessageBox.critical(self, "处理出错", error_msg)
        self._cleanup_worker()

    def _cleanup_worker(self):
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait(3000)
            self._worker_thread = None
            self._worker = None

    def _set_state(self, state: PipelineState):
        self._pipeline_state = state
        is_idle = state in (
            PipelineState.IDLE, PipelineState.COMPLETE,
            PipelineState.ERROR, PipelineState.CANCELLED,
        )
        self.btn_start.setEnabled(is_idle and bool(self._input_path))
        self.btn_cancel.setEnabled(not is_idle)
        if is_idle:
            if _is_url(self._input_path):
                self.btn_start.setText("⬇  开始下载并处理")
            else:
                self.btn_start.setText("▶  开始处理")

    def _speaker_count(self) -> int:
        ids = set(seg.speaker_id for seg in self._segments)
        return len(ids)

    def _on_about(self):
        QMessageBox.about(
            self, "关于 VoiceRole",
            "VoiceRole v1.0\n\n"
            "智能录音角色识别工具\n"
            "自动语音识别 + 说话人分离 + 字幕生成\n\n"
            "技术栈:\n"
            "· faster-whisper — 语音识别\n"
            "· pyannote.audio — 说话人分离\n"
            "· DeepSeek — LLM 智能标注\n"
            "· PyQt6 — 桌面界面\n\n"
            "支持导出 SRT / VTT / TXT 字幕格式"
        )

    def closeEvent(self, event):
        if self._worker and self._pipeline_state not in (
            PipelineState.IDLE, PipelineState.COMPLETE,
            PipelineState.ERROR, PipelineState.CANCELLED,
        ):
            reply = QMessageBox.question(
                self, "确认退出",
                "处理正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self._cleanup_worker()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
