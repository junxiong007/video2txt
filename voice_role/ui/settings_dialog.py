from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QFormLayout, QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from voice_role.config import AppConfig
from voice_role.constants import WHISPER_MODELS
from voice_role.core.diarizer import Diarizer


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        tabs = QTabWidget()
        tabs.addTab(self._asr_tab(), "语音识别")
        tabs.addTab(self._speaker_tab(), "说话人识别")
        tabs.addTab(self._llm_tab(), "LLM 接口")
        tabs.addTab(self._export_tab(), "导出设置")
        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _asr_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        self.asr_model = QComboBox()
        self.asr_model.addItems(WHISPER_MODELS)
        current = self.config.get("asr/model_size", "tiny")
        self.asr_model.setCurrentText(current)
        form.addRow("Whisper 模型:", self.asr_model)

        self.asr_lang = QComboBox()
        self.asr_lang.addItems([
            "auto", "zh", "en", "ja", "ko", "fr", "de", "es", "pt", "ru", "ar"
        ])
        current_lang = self.config.get("asr/language", "auto")
        self.asr_lang.setCurrentText(current_lang)
        form.addRow("语言:", self.asr_lang)

        note = QLabel("模型越大越准确，但处理速度更慢。推荐 tiny 或 base。")
        note.setObjectName("subtitleLabel")
        note.setWordWrap(True)
        form.addRow(note)

        return w

    def _speaker_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # HF Token
        group = QGroupBox("HuggingFace 设置")
        gform = QFormLayout(group)

        self.hf_token = QLineEdit()
        self.hf_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token.setPlaceholderText("输入 hf_xxxx...")
        current_token = self.config.get("hf/token", "")
        if current_token:
            self.hf_token.setText(current_token)
        gform.addRow("HF Token:", self.hf_token)

        btn_row = QHBoxLayout()
        get_btn = QPushButton("获取 Token")
        get_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://huggingface.co/settings/tokens"))
        )
        btn_row.addWidget(get_btn)

        license_btn = QPushButton("接受模型许可")
        license_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://huggingface.co/pyannote/speaker-diarization-3.1")
            )
        )
        btn_row.addWidget(license_btn)
        btn_row.addStretch()
        gform.addRow(btn_row)

        self.hf_status = QLabel("")
        gform.addRow(self.hf_status)

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_hf)
        gform.addRow(test_btn)

        layout.addWidget(group)

        note = QLabel(
            "说话人识别需要 HuggingFace 账号和有效的 token。\n"
            "1. 在 HuggingFace 注册账号\n"
            "2. 创建 token（Settings → Access Tokens）\n"
            "3. 接受 pyannote 模型的使用许可协议\n"
            "如未配置，程序将使用单说话人模式。"
        )
        note.setObjectName("subtitleLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

        return w

    def _llm_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        self.llm_enabled = QCheckBox("启用 LLM 智能标注")
        self.llm_enabled.setChecked(self.config.get("llm/enabled", False))
        form.addRow(self.llm_enabled)

        self.llm_api_key = QLineEdit()
        self.llm_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.llm_api_key.setPlaceholderText("sk-xxxx...")
        current_key = self.config.get("llm/api_key", "")
        if current_key:
            self.llm_api_key.setText(current_key)
        form.addRow("API Key:", self.llm_api_key)

        self.llm_base_url = QLineEdit()
        self.llm_base_url.setText(self.config.get("llm/base_url", "https://api.deepseek.com/v1"))
        form.addRow("Base URL:", self.llm_base_url)

        self.llm_model = QComboBox()
        self.llm_model.addItems(["deepseek-chat", "deepseek-reasoner"])
        self.llm_model.setEditable(True)
        self.llm_model.setCurrentText(self.config.get("llm/model_name", "deepseek-chat"))
        form.addRow("模型:", self.llm_model)

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_llm)
        form.addRow(test_btn)

        self.llm_status = QLabel("")
        form.addRow(self.llm_status)

        note = QLabel(
            "LLM 可自动判断说话人性别并生成中文标签（男一、女二等）。\n"
            "不启用时，说话人标签将显示为 SPEAKER_00 等。"
        )
        note.setObjectName("subtitleLabel")
        note.setWordWrap(True)
        form.addRow(note)

        return w

    def _export_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        self.export_fmt = QComboBox()
        self.export_fmt.addItems(["srt", "vtt", "txt"])
        self.export_fmt.setCurrentText(self.config.get("export/default_format", "srt"))
        form.addRow("默认导出格式:", self.export_fmt)

        self.export_prefix = QComboBox()
        self.export_prefix.addItems(["chinese", "numeric"])
        prefix_map = {"chinese": "男一/女二（中文）", "numeric": "Speaker 1 / Speaker 2（英文数字）"}
        for i in range(self.export_prefix.count()):
            val = self.export_prefix.itemText(i)
            if val in prefix_map:
                self.export_prefix.setItemText(i, prefix_map[val])
        current_prefix = self.config.get("export/speaker_prefix", "chinese")
        idx = self.export_prefix.findText("chinese") if current_prefix == "chinese" else 1
        if idx >= 0:
            self.export_prefix.setCurrentIndex(idx)
        form.addRow("说话人前缀:", self.export_prefix)

        self.max_dur = QDoubleSpinBox()
        self.max_dur.setRange(3, 15)
        self.max_dur.setValue(self.config.get("export/max_duration", 7.0))
        self.max_dur.setSuffix(" 秒")
        form.addRow("最大字幕时长:", self.max_dur)

        self.merge_gap = QDoubleSpinBox()
        self.merge_gap.setRange(0.5, 5.0)
        self.merge_gap.setSingleStep(0.5)
        self.merge_gap.setValue(self.config.get("export/merge_gap", 1.5))
        self.merge_gap.setSuffix(" 秒")
        form.addRow("合并间隔阈值:", self.merge_gap)

        return w

    def _save(self):
        self.config.set("asr/model_size", self.asr_model.currentText())
        self.config.set("asr/language", self.asr_lang.currentText())
        self.config.set("hf/token", self.hf_token.text())
        self.config.set("llm/enabled", self.llm_enabled.isChecked())
        self.config.set("llm/api_key", self.llm_api_key.text())
        self.config.set("llm/base_url", self.llm_base_url.text())
        self.config.set("llm/model_name", self.llm_model.currentText())
        self.config.set("export/default_format", self.export_fmt.currentText())
        self.config.set("export/max_duration", self.max_dur.value())
        self.config.set("export/merge_gap", self.merge_gap.value())
        self.accept()

    def _test_hf(self):
        token = self.hf_token.text().strip()
        if not token:
            self.hf_status.setText("请输入 token")
            self.hf_status.setObjectName("errorLabel")
            self.hf_status.style().unpolish(self.hf_status)
            self.hf_status.style().polish(self.hf_status)
            return
        d = Diarizer(hf_token=token)
        if d.is_available():
            self.hf_status.setText("连接成功")
            self.hf_status.setStyleSheet(f"color: #27AE60; font-weight: bold;")
        else:
            self.hf_status.setText("验证失败：请确认 token 有效且已接受模型许可")
            self.hf_status.setObjectName("errorLabel")
            self.hf_status.style().unpolish(self.hf_status)
            self.hf_status.style().polish(self.hf_status)

    def _test_llm(self):
        api_key = self.llm_api_key.text().strip()
        base_url = self.llm_base_url.text().strip()
        if not api_key:
            self.llm_status.setText("请输入 API Key")
            self.llm_status.setObjectName("errorLabel")
            self.llm_status.style().unpolish(self.llm_status)
            self.llm_status.style().polish(self.llm_status)
            return
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            client.models.list()
            self.llm_status.setText("连接成功")
            self.llm_status.setStyleSheet(f"color: #27AE60; font-weight: bold;")
        except Exception as e:
            self.llm_status.setText(f"连接失败: {e}")
            self.llm_status.setObjectName("errorLabel")
            self.llm_status.style().unpolish(self.llm_status)
            self.llm_status.style().polish(self.llm_status)
