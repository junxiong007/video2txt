import subprocess
import shutil
from pathlib import Path
from voice_role.constants import SAMPLE_RATE


class FFmpegNotFoundError(Exception):
    pass


def _find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    # Check common Windows install locations
    for loc in [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("D:/ffmpeg/bin/ffmpeg.exe"),
        Path("D:/ffmpeg-8.1-essentials_build/bin/ffmpeg.exe"),
        Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path.home() / "Downloads" / "ffmpeg-8.1-essentials_build" / "bin" / "ffmpeg.exe",
    ]:
        if loc.exists():
            return str(loc)
    # Auto-search in Downloads and D:/ for any ffmpeg*/bin/ffmpeg.exe
    for base in [Path.home() / "Downloads", Path("D:/")]:
        try:
            for p in base.glob("ffmpeg*/bin/ffmpeg.exe"):
                return str(p)
        except OSError:
            pass
    raise FFmpegNotFoundError(
        "未找到 FFmpeg。请安装 FFmpeg 并确保它在系统 PATH 中。\n"
        "下载地址: https://ffmpeg.org/download.html"
    )


def extract_audio(input_path: str | Path, output_dir: str | Path) -> Path:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_path.stem}_audio.wav"

    ffmpeg = _find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(input_path),
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-sample_fmt", "s16",
        "-hide_banner", "-loglevel", "error",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 提取音频失败: {result.stderr}")

    return output_path


def get_media_duration(input_path: str | Path) -> float:
    input_path = str(input_path)
    ffmpeg = _find_ffmpeg()
    # Use ffprobe if available, otherwise ffmpeg
    ffprobe = str(Path(ffmpeg).parent / "ffprobe.exe")
    if shutil.which(ffprobe) or Path(ffprobe).exists():
        probe_cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path,
        ]
    else:
        probe_cmd = [
            ffmpeg, "-i", input_path,
            "-hide_banner", "-loglevel", "error",
            "-f", "null", "-",
        ]

    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip().split("\n")[-1])
    except (ValueError, IndexError):
        return 0.0
