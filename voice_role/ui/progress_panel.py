from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QTextEdit,
)
from PyQt6.QtCore import Qt
from voice_role.constants import PipelineState, STEP_NAMES
from voice_role.ui.theme import COLORS


class ProgressPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._state = PipelineState.IDLE
        self._steps = list(STEP_NAMES.keys())
        self._step_labels = {}
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Step indicators row
        steps_row = QHBoxLayout()
        steps_row.setSpacing(4)
        for step in self._steps:
            lbl = QLabel(STEP_NAMES.get(step, step.value))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 10pt; "
                f"padding: 2px 6px;"
            )
            steps_row.addWidget(lbl)
            self._step_labels[step] = lbl
        layout.addLayout(steps_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setObjectName("subtitleLabel")
        layout.addWidget(self.status_label)

        # Log area (collapsed by default)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(80)
        self.log_area.setVisible(False)
        self.log_area.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 4px; "
            f"font-family: Consolas; font-size: 9pt; padding: 4px;"
        )
        layout.addWidget(self.log_area)

    def set_state(self, state: PipelineState):
        self._state = state
        for step, lbl in self._step_labels.items():
            if step == state:
                lbl.setStyleSheet(
                    f"color: {COLORS['gold_dark']}; font-weight: bold; font-size: 10pt; "
                    f"border-bottom: 2px solid {COLORS['gold_primary']}; padding: 2px 6px;"
                )
            elif hasattr(self, "_completed_steps") and step in self._completed_steps:
                lbl.setStyleSheet(
                    f"color: {COLORS['success']}; font-size: 10pt; padding: 2px 6px;"
                )
            else:
                lbl.setStyleSheet(
                    f"color: {COLORS['text_secondary']}; font-size: 10pt; padding: 2px 6px;"
                )

    def set_progress(self, percent: int, message: str = ""):
        self.progress_bar.setValue(percent)
        if message:
            self.status_label.setText(message)
            self.log_area.append(message)
            self.log_area.moveCursor(self.log_area.textCursor().MoveOperation.End)

    def reset(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.log_area.clear()
        self._completed_steps = set()
        for lbl in self._step_labels.values():
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 10pt; padding: 2px 6px;"
            )
