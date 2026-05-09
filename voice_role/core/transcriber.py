import warnings
from pathlib import Path
from faster_whisper import WhisperModel
from voice_role.constants import WHISPER_MODELS
from voice_role.models.segment import WordTimestamp


class Transcriber:
    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        if model_size not in WHISPER_MODELS:
            model_size = "tiny"
        self.model_size = model_size
        self._model = None
        self._device = device
        self._compute_type = compute_type

    def _ensure_model(self):
        if self._model is None:
            self._model = WhisperModel(
                self.model_size,
                device=self._device,
                compute_type=self._compute_type,
            )

    def transcribe(self, audio_path: str | Path, language: str | None = None) -> list[WordTimestamp]:
        self._ensure_model()
        audio_path = str(audio_path)

        segments, info = self._model.transcribe(
            audio_path,
            word_timestamps=True,
            language=language if language and language != "auto" else None,
            vad_filter=False,
            beam_size=5,
        )

        words = []
        for seg in segments:
            if seg.words:
                for w in seg.words:
                    words.append(WordTimestamp(
                        word=w.word.strip(),
                        start=w.start,
                        end=w.end,
                        confidence=w.probability,
                    ))
            else:
                # No word timestamps; use segment-level
                words.append(WordTimestamp(
                    word=seg.text.strip(),
                    start=seg.start,
                    end=seg.end,
                    confidence=1.0,
                ))

        return words
