"""CapCut-ready .SRT subtitle generator (anti-CapCut-Pro paywall helper)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.schemas import BlueprintResponse


@dataclass
class SubtitleCue:
    index: int
    start_sec: float
    end_sec: float
    text: str


def format_srt_timestamp(seconds: float) -> str:
    sec = max(0.0, seconds)
    hours = int(sec // 3600)
    minutes = int((sec % 3600) // 60)
    secs = int(sec % 60)
    millis = int(round((sec - int(sec)) * 1000))
    if millis >= 1000:
        secs += 1
        millis -= 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _split_into_short_phrases(text: str, max_words: int = 4) -> list[str]:
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if not words:
        return []
    phrases: list[str] = []
    for i in range(0, len(words), max_words):
        phrases.append(" ".join(words[i : i + max_words]))
    return phrases


def build_srt_from_blueprint(bp: BlueprintResponse, max_words_per_cue: int = 4) -> str:
    """Build a timed .SRT subtitle file aligned to each scene's duration (3-4 words per line)."""
    cues: list[SubtitleCue] = []
    cursor = 0.0
    cue_idx = 1

    for scene in bp.scenes:
        dur = float(max(1, scene.duration_sec))
        phrases = _split_into_short_phrases(scene.vo_script_id, max_words=max_words_per_cue)
        if not phrases:
            cursor += dur
            continue

        weights = [max(1, len(p)) for p in phrases]
        total_w = float(sum(weights))
        sub_cursor = cursor
        for phrase, w in zip(phrases, weights):
            seg_dur = (w / total_w) * dur
            start = sub_cursor
            end = min(cursor + dur, sub_cursor + seg_dur)
            cues.append(
                SubtitleCue(
                    index=cue_idx,
                    start_sec=start,
                    end_sec=max(start + 0.2, end),
                    text=phrase,
                )
            )
            cue_idx += 1
            sub_cursor += seg_dur

        cursor += dur

    return render_cues_to_srt(cues)


def render_cues_to_srt(cues: list[SubtitleCue]) -> str:
    blocks: list[str] = []
    for idx, c in enumerate(cues, start=1):
        blocks.append(
            f"{idx}\n{format_srt_timestamp(c.start_sec)} --> {format_srt_timestamp(c.end_sec)}\n{c.text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def save_blueprint_srt(bp: BlueprintResponse, output_srt: Path) -> Path:
    output_srt.parent.mkdir(parents=True, exist_ok=True)
    output_srt.write_text(build_srt_from_blueprint(bp), encoding="utf-8")
    return output_srt
