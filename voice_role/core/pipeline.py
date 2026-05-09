import threading
import uuid
import tempfile
from pathlib import Path
from datetime import datetime

from voice_role.config import AppConfig
from voice_role.constants import PipelineState, STEP_NAMES
from voice_role.models.segment import PipelineResult
from voice_role.core.audio_extractor import extract_audio
from voice_role.core.vad import VAD
from voice_role.core.transcriber import Transcriber
from voice_role.core.diarizer import Diarizer, HFTokenError
from voice_role.core.aligner import align
from voice_role.core.llm_refiner import LLMRefiner
from voice_role.core.exporter import export_srt, export_vtt, export_txt


class Pipeline:
    def __init__(self, config: AppConfig, progress_callback=None, state_callback=None, cancel_event=None):
        self.config = config
        self.progress_callback = progress_callback or (lambda p, msg: None)
        self.state_callback = state_callback or (lambda s: None)
        self.cancel_flag = cancel_event or threading.Event()

    def cancel(self):
        self.cancel_flag.set()

    def _check_cancel(self):
        if self.cancel_flag.is_set():
            raise InterruptedError("用户取消")

    def run(self, input_path: str | Path) -> PipelineResult:
        input_path = Path(input_path)
        result = PipelineResult(audio_path=str(input_path))
        temp_dir = Path(tempfile.gettempdir()) / "voicerole" / str(uuid.uuid4())[:8]
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Extract audio
            self._check_cancel()
            self.state_callback(PipelineState.EXTRACTING)
            self.progress_callback(5, "正在提取音频...")
            wav_path = extract_audio(input_path, temp_dir)
            result.audio_path = str(wav_path)

            # Step 2: VAD
            self._check_cancel()
            self.state_callback(PipelineState.DETECTING_VOICE)
            self.progress_callback(15, "正在检测语音活动...")
            vad = VAD()
            speech_segments = vad.detect_speech(wav_path)

            # Step 3: ASR Transcription
            self._check_cancel()
            self.state_callback(PipelineState.TRANSCRIBING)
            self.progress_callback(25, "正在进行语音识别...")
            model_size = self.config.get("asr/model_size", "tiny")
            language = self.config.get("asr/language", "auto")
            transcriber = Transcriber(model_size=model_size)
            words = transcriber.transcribe(wav_path, language=language)
            self.progress_callback(50, f"语音识别完成，共 {len(words)} 个词")

            # Step 4: Diarization
            self._check_cancel()
            self.state_callback(PipelineState.DIARIZING)
            self.progress_callback(55, "正在识别说话人...")
            hf_token = self.config.get("hf/token", "")
            diarizer = Diarizer(hf_token=hf_token)
            if diarizer.is_available():
                speaker_segments = diarizer.diarize(wav_path)
                self.progress_callback(70, f"识别到 {len(set(s.speaker_id for s in speaker_segments))} 个说话人")
            else:
                speaker_segments = []
                self.progress_callback(70, "未配置 HuggingFace token，跳过说话人识别")

            # Step 5: Alignment
            self._check_cancel()
            self.state_callback(PipelineState.ALIGNING)
            self.progress_callback(75, "正在对齐字幕...")
            segments = align(words, speaker_segments)
            self.progress_callback(85, f"已生成 {len(segments)} 条字幕")

            # Step 6: LLM Refinement (optional)
            if self.config.get("llm/enabled", False):
                self._check_cancel()
                self.state_callback(PipelineState.REFINING)
                self.progress_callback(88, "正在通过 LLM 智能标注说话人...")
                api_key = self.config.get("llm/api_key", "")
                base_url = self.config.get("llm/base_url", "")
                model = self.config.get("llm/model_name", "")
                if api_key:
                    refiner = LLMRefiner(api_key=api_key, base_url=base_url, model=model)
                    segments = refiner.refine(segments)
                    self.progress_callback(95, "LLM 标注完成")
                else:
                    self.progress_callback(95, "未配置 LLM API key，使用默认说话人标签")

            result.segments = segments
            self.state_callback(PipelineState.COMPLETE)
            self.progress_callback(100, "处理完成！")

        except InterruptedError:
            self.state_callback(PipelineState.CANCELLED)
            self.progress_callback(0, "已取消")
            result.errors.append("用户取消处理")
        except HFTokenError as e:
            self.state_callback(PipelineState.ERROR)
            self.progress_callback(0, str(e))
            result.errors.append(str(e))
        except Exception as e:
            self.state_callback(PipelineState.ERROR)
            self.progress_callback(0, f"处理出错: {e}")
            result.errors.append(str(e))

        return result
