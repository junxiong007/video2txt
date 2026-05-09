from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from voice_role.models.segment import TranscriptionSegment
from voice_role.ui.theme import COLORS, SPEAKER_COLORS


class SubtitleTable(QTableWidget):
    segment_edited = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._segments: list[TranscriptionSegment] = []
        self._speaker_colors: dict[str, str] = {}
        self._setup()

    def _setup(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["#", "开始", "结束", "时长", "说话人", "文字内容"])
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 80)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)

    def load_segments(self, segments: list[TranscriptionSegment]):
        self._segments = segments
        self._assign_colors()
        self.setRowCount(len(segments))
        for i, seg in enumerate(segments):
            self._set_row(i, seg)
        self.segment_edited.emit()

    def _assign_colors(self):
        self._speaker_colors.clear()
        for seg in self._segments:
            if seg.speaker_id not in self._speaker_colors:
                color_idx = len(self._speaker_colors) % len(SPEAKER_COLORS)
                self._speaker_colors[seg.speaker_id] = SPEAKER_COLORS[color_idx]

    def _format_time(self, seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"

    def _set_row(self, row: int, seg: TranscriptionSegment):
        color = self._speaker_colors.get(seg.speaker_id, COLORS["text_secondary"])

        items = [
            (str(row + 1), False),
            (self._format_time(seg.start), False),
            (self._format_time(seg.end), False),
            (f"{seg.duration:.1f}s", False),
            (seg.speaker_label or seg.speaker_id, True),
            (seg.text, True),
        ]
        for col, (text, editable) in enumerate(items):
            item = QTableWidgetItem(text)
            if not editable:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if col == 4:  # Speaker column — colored
                item.setForeground(QColor(color))
                item.setData(Qt.ItemDataRole.UserRole, seg.speaker_id)
            if col == 5:  # Text column
                item.setData(Qt.ItemDataRole.UserRole, seg)
            self.setItem(row, col, item)

    def _context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row < 0 or row >= len(self._segments):
            return

        menu = QMenu(self)
        merge_action = QAction("与下一行合并", self)
        merge_action.triggered.connect(lambda: self._merge_row(row))
        menu.addAction(merge_action)

        edit_label_action = QAction("修改说话人标签...", self)
        edit_label_action.triggered.connect(lambda: self._edit_label(row))
        menu.addAction(edit_label_action)

        menu.exec(self.viewport().mapToGlobal(pos))

    def _merge_row(self, row: int):
        if row + 1 >= len(self._segments):
            return
        cur = self._segments[row]
        nxt = self._segments.pop(row + 1)
        cur.end = nxt.end
        cur.text = cur.text + nxt.text
        cur.words.extend(nxt.words)
        self.load_segments(self._segments)

    def _edit_label(self, row: int):
        from PyQt6.QtWidgets import QInputDialog
        seg = self._segments[row]
        new_label, ok = QInputDialog.getText(
            self, "修改说话人标签",
            f"为 {seg.speaker_id} 输入新标签:",
            text=seg.speaker_label or seg.speaker_id,
        )
        if ok and new_label:
            for s in self._segments:
                if s.speaker_id == seg.speaker_id:
                    s.speaker_label = new_label
            self.load_segments(self._segments)
