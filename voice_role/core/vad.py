import numpy as np
import soundfile as sf
from pathlib import Path


class VAD:
    def __init__(self):
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from silero_vad import load_silero_vad
            self._model = load_silero_vad(onnx=True)

    def detect_speech(self, audio_path: str | Path) -> list[tuple[float, float]]:
        self._ensure_model()
        audio_path = str(audio_path)

        audio, sr = sf.read(audio_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz if needed
        if sr != 16000:
            import torch
            import torchaudio.functional as F
            waveform = torch.from_numpy(audio).unsqueeze(0)
            waveform = F.resample(waveform, sr, 16000)
            audio = waveform.squeeze(0).numpy()
            sr = 16000

        from silero_vad import get_speech_timestamps
        chunks = get_speech_timestamps(
            audio, self._model,
            sampling_rate=sr,
            min_speech_duration_ms=300,
            min_silence_duration_ms=400,
            return_seconds=True,
        )

        if not chunks:
            return [(0.0, len(audio) / sr)]

        # Merge adjacent segments with gap < 0.5s
        merged = []
        for ch in chunks:
            start = ch["start"]
            end = ch["end"]
            if merged and start - merged[-1][1] < 0.5:
                merged[-1] = (merged[-1][0], end)
            else:
                merged.append((start, end))

        return merged
