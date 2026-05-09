import warnings
import numpy as np
import soundfile as sf
import torch
from pathlib import Path
from voice_role.models.segment import SpeakerSegment

warnings.filterwarnings("ignore", message=".*Failed to load libtorchcodec.*")


class HFTokenError(Exception):
    pass


class Diarizer:
    def __init__(self, hf_token: str = ""):
        self.hf_token = hf_token
        self._pipeline = None
        self._available = None  # None = not checked, True/False

    def is_available(self) -> bool:
        if self._available is None:
            if not self.hf_token:
                self._available = False
            else:
                try:
                    self._load_pipeline()
                    self._available = True
                except Exception:
                    self._available = False
        return self._available

    def _load_pipeline(self):
        if self._pipeline is not None:
            return
        if not self.hf_token:
            raise HFTokenError("缺少 HuggingFace token，无法进行说话人识别。请在设置中配置 HF token。")
        from pyannote.audio import Pipeline
        self._pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=self.hf_token,
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._pipeline.to(device)

    def diarize(self, audio_path: str | Path) -> list[SpeakerSegment]:
        if not self.is_available():
            return []
        self._load_pipeline()

        audio_path = str(audio_path)

        # pyannote 4.x can use torchcodec for file loading, but if FFmpeg
        # isn't installed (torchcodec fails), we preload audio as a waveform dict
        try:
            diarization = self._pipeline(audio_path)
        except Exception:
            # Fallback: load audio manually and pass as waveform
            audio, sr = sf.read(audio_path, dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            waveform = torch.from_numpy(audio).unsqueeze(0)
            if sr != 16000:
                import torchaudio.functional as F
                waveform = F.resample(waveform, sr, 16000)
                sr = 16000
            audio_input = {"waveform": waveform, "sample_rate": sr}
            diarization = self._pipeline(audio_input)

        # pyannote 4.x returns DiarizeOutput (wrapper), 3.x returns Annotation directly
        if hasattr(diarization, "exclusive_speaker_diarization"):
            ann = diarization.exclusive_speaker_diarization
        else:
            ann = diarization

        segments = []
        for turn, _, speaker in ann.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                speaker_id=speaker,
                start=turn.start,
                end=turn.end,
            ))

        return segments
