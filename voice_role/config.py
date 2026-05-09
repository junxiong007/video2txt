import base64
import json
from pathlib import Path
from PyQt6.QtCore import QSettings

SETTINGS_DIR = Path.home() / ".voicerole"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


DEFAULTS = {
    "asr/model_size": "tiny",
    "asr/language": "auto",
    "hf/token": "",
    "llm/api_key": "",
    "llm/base_url": "https://api.deepseek.com/v1",
    "llm/model_name": "deepseek-chat",
    "llm/enabled": False,
    "export/default_format": "srt",
    "export/speaker_prefix": "chinese",  # "chinese" or "numeric"
    "export/max_duration": 7.0,
    "export/merge_gap": 1.5,
}


def _obfuscate(text: str) -> str:
    if not text:
        return ""
    return base64.b64encode(text.encode()).decode()


def _deobfuscate(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text.encode()).decode()
    except Exception:
        return ""


class AppConfig:
    def __init__(self):
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self._data = {}
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        for key, val in DEFAULTS.items():
            if key not in self._data:
                self._data[key] = val

    def save(self):
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        val = self._data.get(key, DEFAULTS.get(key, default))
        if key in ("hf/token", "llm/api_key"):
            return _deobfuscate(val) if val else ""
        return val

    def set(self, key: str, value):
        if key in ("hf/token", "llm/api_key"):
            self._data[key] = _obfuscate(str(value)) if value else ""
        else:
            self._data[key] = value
        self.save()
