from PyQt6.QtCore import QObject, pyqtSignal

from voice_role.constants import PipelineState


class PipelineSignals(QObject):
    state_changed = pyqtSignal(PipelineState)
    progress = pyqtSignal(int, str)  # percent, message
    finished = pyqtSignal(list)      # list[TranscriptionSegment]
    error_occurred = pyqtSignal(str)
