# video2txt
把语音视频文件或者网络链接转换成字幕，分不同角色


启动方式

方式一：双击run.bat


方式二：命令行

python -m venv venv


venv\Scripts\activate


pip install -r requirements.txt  #安装依赖包List


venv\Scripts\activate python main.py



需要手动做这件事

1- 安装 FFmpeg（必需！音频/视频提取依赖）： - 下载: https://ffmpeg.org/download.html - Windows 安装后将 ffmpeg.exe 所在目录添加到系统 PATH

2- HuggingFace Token（可选，说话人识别需要）： - 在设置→说话人识别标签页中配置 - 未配置时所有语音归为单说话人

3- （可选）设置你的大模型的API_KEY。默认为deepseek，也可以在代码内修改其他模型接口。

4- 测试：拖放一段多人对话的mp3/mp4文件，点击“开始处理”。



处理流程

音频/视频 → 提取16kHz WAV → VAD语音检测 → 更快的耳语解析 → pyannote说话人分离 → 时间对齐 → DeepSeek LLM智能标注(男一/女二) → 导出SRT/VTT/TXT



【后续可以自行添加 翻译功能。去年年初已经实现，项目代码不知放哪了。有兴趣可以自行vibe coding。】
