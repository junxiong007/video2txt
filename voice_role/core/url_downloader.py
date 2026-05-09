import logging
import threading
from pathlib import Path
from typing import Callable


class _NullLogger(logging.Logger):
    def handle(self, record):
        pass


class _DownloadCancelled(Exception):
    pass


def download_audio(
    url: str,
    output_dir: Path,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> Path:
    """Download audio from a URL using yt-dlp.

    Returns the path to the downloaded audio file.
    Raises RuntimeError on download failure, InterruptedError on cancel.
    """
    if progress_callback is None:
        progress_callback = lambda p, msg: None
    if cancel_event is None:
        cancel_event = threading.Event()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title).200s.%(ext)s")
    _finished_file = None

    def _progress_hook(d):
        nonlocal _finished_file
        if cancel_event.is_set():
            raise _DownloadCancelled()
        status = d.get("status", "")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            pct = d["downloaded_bytes"] / total * 100
            speed = d.get("speed", 0) or 0
            speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else ""
            eta = d.get("eta", 0) or 0
            eta_str = f"剩余 {eta}s" if eta else ""
            progress_callback(pct, f"{pct:.0f}%  {speed_str}  {eta_str}".strip())
        elif status == "finished":
            _finished_file = d.get("filename", "")
            progress_callback(100, "下载完成")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "progress_hooks": [_progress_hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "logger": _NullLogger("yt_dlp"),
    }

    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("未安装 yt-dlp，请在终端运行: pip install yt-dlp")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except _DownloadCancelled:
        raise InterruptedError("下载已取消")
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).lower()
        if any(k in msg for k in ("403", "unavailable", "private", "removed", "deleted")):
            raise RuntimeError("无法访问该视频（视频不存在、已删除或需要登录）")
        if "no format" in msg or "no video format" in msg:
            raise RuntimeError("该视频没有可用的音频流")
        if "unsupported" in msg:
            raise RuntimeError("不支持的链接格式，请检查网址是否正确")
        raise RuntimeError(f"下载失败: {e}")
    except yt_dlp.utils.ExtractorError as e:
        raise RuntimeError(f"无法解析该链接，网站可能不受支持: {e}")
    except OSError as e:
        raise RuntimeError(f"网络连接失败，请检查网络: {e}")
    except InterruptedError:
        raise
    except Exception as e:
        raise RuntimeError(f"下载失败: {e}")

    if cancel_event.is_set():
        raise InterruptedError("下载已取消")

    # Find the downloaded file
    if _finished_file and Path(_finished_file).exists():
        return Path(_finished_file)

    # Fallback: find the newest file in output_dir
    files = sorted(output_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    if files:
        return files[0]

    raise RuntimeError("下载完成但未找到输出文件")
