import threading
import uuid
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject

from voice_role.config import AppConfig
from voice_role.constants import PipelineState
from voice_role.core.pipeline import Pipeline
from voice_role.workers.signals import PipelineSignals


class PipelineWorker(QObject):
    def __init__(self, config: AppConfig, input_path: str, is_url: bool = False):
        super().__init__()
        self.config = config
        self.input_path = input_path
        self.is_url = is_url
        self.signals = PipelineSignals()
        self._pipeline: Pipeline | None = None
        self._cancel_event = threading.Event()

    def run(self):
        actual_input = self.input_path

        if self.is_url:
            self.signals.state_changed.emit(PipelineState.DOWNLOADING)
            dl_dir = Path(tempfile.gettempdir()) / "voicerole" / "downloads" \
                     / str(uuid.uuid4())[:8]
            dl_dir.mkdir(parents=True, exist_ok=True)

            try:
                from voice_role.core.url_downloader import download_audio
                downloaded = download_audio(
                    self.input_path,
                    dl_dir,
                    progress_callback=self._on_download_progress,
                    cancel_event=self._cancel_event,
                )
                actual_input = str(downloaded)
                self._on_progress(5, "下载完成，开始提取音频...")
            except InterruptedError:
                self.signals.state_changed.emit(PipelineState.CANCELLED)
                self.signals.progress.emit(0, "下载已取消")
                return
            except Exception as e:
                self.signals.error_occurred.emit(str(e))
                return

        self._pipeline = Pipeline(
            config=self.config,
            progress_callback=self._on_progress,
            state_callback=self._on_state_changed,
            cancel_event=self._cancel_event,
        )
        try:
            result = self._pipeline.run(actual_input)
        except Exception as e:
            self.signals.error_occurred.emit(str(e))
            return

        if result.errors:
            self.signals.error_occurred.emit("; ".join(result.errors))
        else:
            self.signals.finished.emit(result.segments)

    def cancel(self):
        self._cancel_event.set()
        if self._pipeline:
            self._pipeline.cancel()

    def _on_download_progress(self, percent: float, message: str):
        mapped = int(percent * 0.05)
        self._on_progress(mapped, f"下载: {message}")

    def _on_progress(self, percent: int, message: str):
        self.signals.progress.emit(percent, message)

    def _on_state_changed(self, state):
        self.signals.state_changed.emit(state)
