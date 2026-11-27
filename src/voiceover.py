"""Indonesian TTS helper (edge-tts) exporting both vo_capcut.mp3 and word-synced vo_capcut.srt."""

from __future__ import annotations

import asyncio
import concurrent.futures
from pathlib import Path

import edge_tts

from src.srt_export import SubtitleCue, render_cues_to_srt


async def _synthesize_mp3_and_word_cues_async(
    text: str,
    output_mp3: Path,
    voice: str,
    rate: str,
    max_words_per_cue: int = 4,
) -> list[SubtitleCue]:
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text.strip(),
        voice=voice,
        rate=rate,
        boundary="WordBoundary",
    )
    words: list[tuple[str, float, float]] = []
    with output_mp3.open("wb") as audio_fh:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                audio_fh.write(chunk["data"])
            elif ctype == "WordBoundary":
                w_txt = str(chunk.get("text", "")).strip()
                start = float(chunk.get("offset", 0)) / 10_000_000.0
                dur = float(chunk.get("duration", 0)) / 10_000_000.0
                if w_txt:
                    words.append((w_txt, start, start + max(0.08, dur)))

    cues: list[SubtitleCue] = []
    for idx in range(0, len(words), max_words_per_cue):
        group = words[idx : idx + max_words_per_cue]
        cues.append(
            SubtitleCue(
                index=len(cues) + 1,
                start_sec=group[0][1],
                end_sec=max(group[0][1] + 0.2, group[-1][2]),
                text=" ".join(item[0] for item in group),
            )
        )
    return cues


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def synthesize_vo_mp3(
    text: str,
    output_mp3: Path,
    voice: str = "id-ID-GadisNeural",
    rate: str = "+6%",
    output_srt: Path | None = None,
) -> Path:
    """Synthesize Indonesian VO MP3 (and optional word-accurate .SRT) ready for CapCut."""
    cues: list[SubtitleCue] = _run_async(
        _synthesize_mp3_and_word_cues_async(
            text=text,
            output_mp3=output_mp3,
            voice=voice,
            rate=rate,
        )
    )
    if output_srt is not None and cues:
        output_srt.parent.mkdir(parents=True, exist_ok=True)
        output_srt.write_text(render_cues_to_srt(cues), encoding="utf-8")
    return output_mp3
