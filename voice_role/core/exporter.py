from pathlib import Path
from voice_role.models.segment import TranscriptionSegment


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def export_srt(segments: list[TranscriptionSegment], output_path: str | Path):
    output_path = Path(output_path)
    lines = []
    for i, seg in enumerate(segments, 1):
        label = seg.speaker_label or seg.speaker_id
        prefix = f"{label}: " if label else ""
        lines.append(str(i))
        lines.append(f"{_format_srt_time(seg.start)} --> {_format_srt_time(seg.end)}")
        lines.append(f"{prefix}{seg.text}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def export_vtt(segments: list[TranscriptionSegment], output_path: str | Path):
    output_path = Path(output_path)
    lines = ["WEBVTT", ""]
    for seg in segments:
        label = seg.speaker_label or seg.speaker_id
        lines.append(f"{_format_vtt_time(seg.start)} --> {_format_vtt_time(seg.end)}")
        if label:
            lines.append(f"<v {label}>{seg.text}")
        else:
            lines.append(seg.text)
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def export_txt(segments: list[TranscriptionSegment], output_path: str | Path):
    output_path = Path(output_path)
    lines = []
    for seg in segments:
        label = seg.speaker_label or seg.speaker_id
        prefix = f"{label}: " if label else ""
        start = _format_vtt_time(seg.start)
        end = _format_vtt_time(seg.end)
        lines.append(f"[{start} - {end}] {prefix}{seg.text}")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def format_transcript(segments: list[TranscriptionSegment]) -> str:
    lines = []
    for seg in segments:
        label = seg.speaker_label or seg.speaker_id
        prefix = f"{label}: " if label else ""
        lines.append(f"{prefix}{seg.text}")
    return "\n".join(lines)
