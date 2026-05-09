from enum import Enum
from pathlib import Path


class PipelineState(Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    DETECTING_VOICE = "detecting_voice"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    ALIGNING = "aligning"
    REFINING = "refining"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"


WHISPER_MODELS = ["tiny", "base", "small", "medium"]

SUPPORTED_AUDIO = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma")
SUPPORTED_VIDEO = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv")
SUPPORTED_FORMATS = SUPPORTED_AUDIO + SUPPORTED_VIDEO

SAMPLE_RATE = 16000

TEMP_DIR = Path.home() / ".voicerole" / "temp"

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

MAX_SUBTITLE_DURATION = 7.0
MERGE_GAP_THRESHOLD = 1.5

STEP_NAMES = {
    PipelineState.DOWNLOADING: "下载音频",
    PipelineState.EXTRACTING: "提取音频",
    PipelineState.DETECTING_VOICE: "检测语音活动",
    PipelineState.TRANSCRIBING: "语音识别",
    PipelineState.DIARIZING: "说话人识别",
    PipelineState.ALIGNING: "对齐字幕",
    PipelineState.REFINING: "LLM 智能标注",
}
