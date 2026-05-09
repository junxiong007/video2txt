from voice_role.models.segment import WordTimestamp, SpeakerSegment, TranscriptionSegment


def _find_speaker(word: WordTimestamp, speakers: list[SpeakerSegment]) -> str | None:
    """Find which speaker a word belongs to by temporal overlap."""
    best_id = None
    best_overlap = 0.0
    word_dur = word.end - word.start
    for spk in speakers:
        overlap_start = max(word.start, spk.start)
        overlap_end = min(word.end, spk.end)
        overlap = max(0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_id = spk.speaker_id

    if best_overlap <= 0 or (word_dur > 0 and best_overlap / word_dur < 0.3):
        # Word mostly outside any speaker segment — find nearest
        min_dist = float("inf")
        for spk in speakers:
            # Distance from word center to segment center
            wc = (word.start + word.end) / 2
            sc = (spk.start + spk.end) / 2
            dist = abs(wc - sc)
            if dist < min_dist:
                min_dist = dist
                best_id = spk.speaker_id

    return best_id


def align(words: list[WordTimestamp], speakers: list[SpeakerSegment]) -> list[TranscriptionSegment]:
    if not speakers:
        # No diarization — assign everything to a default speaker
        return _fallback_single_speaker(words)

    # Build time-indexed speaker lookup for efficiency
    spk_timeline = []
    for spk in speakers:
        spk_timeline.append((spk.start, spk.end, spk.speaker_id))
    spk_timeline.sort()

    # Assign speaker to each word
    for word in words:
        sid = _find_speaker(word, speakers)
        word._speaker_id = sid or "SPEAKER_00"

    # Group consecutive words with same speaker into segments
    segments = []
    i = 0
    while i < len(words):
        sid = getattr(words[i], "_speaker_id", "SPEAKER_00")
        j = i
        while j < len(words) and getattr(words[j], "_speaker_id", "SPEAKER_00") == sid:
            j += 1

        group = words[i:j]
        seg = TranscriptionSegment(
            speaker_id=sid,
            speaker_label=sid,
            text="".join(w.word for w in group),
            start=group[0].start,
            end=group[-1].end,
            words=group,
            confidence=sum(w.confidence for w in group) / len(group),
        )
        segments.append(seg)
        i = j

    # Merge small adjacent segments from same speaker
    segments = _merge_adjacent(segments)
    return segments


def _fallback_single_speaker(words: list[WordTimestamp]) -> list[TranscriptionSegment]:
    sid = "SPEAKER_00"
    segments = []
    for w in words:
        segments.append(TranscriptionSegment(
            speaker_id=sid,
            speaker_label="说话人",
            text=w.word,
            start=w.start,
            end=w.end,
            words=[w],
            confidence=w.confidence,
        ))
    return _merge_adjacent(segments)


def _merge_adjacent(segments: list[TranscriptionSegment], gap_threshold: float = 1.5) -> list[TranscriptionSegment]:
    if not segments:
        return []
    merged = [segments[0]]
    for seg in segments[1:]:
        prev = merged[-1]
        gap = seg.start - prev.end
        if seg.speaker_id == prev.speaker_id and gap < gap_threshold:
            prev.end = seg.end
            prev.text = prev.text + seg.text
            prev.words.extend(seg.words)
            prev.confidence = (prev.confidence + seg.confidence) / 2
        else:
            merged.append(seg)
    return merged
