"""Convert Home Assistant Assist debug events into privacy-safe durations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PipelineObservation:
    complete: bool
    status: str
    stages: dict[str, float]
    error_codes: tuple[str, ...]


def _timestamp(event: dict[str, Any]) -> float | None:
    raw = event.get("timestamp")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def analyze_pipeline_events(events: list[dict[str, Any]]) -> PipelineObservation:
    by_type: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str):
            by_type.setdefault(event_type, []).append(event)

    complete = bool(by_type.get("run-end"))
    error_codes: list[str] = []
    for error in by_type.get("error", []):
        data = error.get("data")
        code = data.get("code") if isinstance(data, dict) else None
        error_codes.append(str(code or "unknown"))

    def first(event_type: str) -> float | None:
        matching = by_type.get(event_type, [])
        return _timestamp(matching[0]) if matching else None

    stages: dict[str, float] = {}

    def duration(name: str, start_type: str, end_type: str) -> None:
        start = first(start_type)
        end = first(end_type)
        if start is not None and end is not None and end >= start:
            stages[name] = end - start

    duration("pipeline", "run-start", "run-end")
    duration("wake_word", "wake_word-start", "wake_word-end")
    duration("stt_total", "stt-start", "stt-end")
    duration("speech", "stt-vad-start", "stt-vad-end")
    duration("stt_after_speech", "stt-vad-end", "stt-end")
    duration("intent", "intent-start", "intent-end")
    duration("intent_first_progress", "intent-start", "intent-progress")
    duration("tts", "tts-start", "tts-end")
    duration("speech_end_to_tts_end", "stt-vad-end", "tts-end")

    return PipelineObservation(
        complete=complete,
        status="error" if error_codes else "success",
        stages=stages,
        error_codes=tuple(error_codes),
    )

