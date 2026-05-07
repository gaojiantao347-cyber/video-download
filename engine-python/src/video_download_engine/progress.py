from __future__ import annotations

from pathlib import Path
from typing import Any

from video_download_engine.protocol import ProgressEvent

_BYTES_PER_KIB = 1024
_BYTES_PER_MIB = _BYTES_PER_KIB * 1024


def build_progress_event(request_id: str, raw: dict[str, Any]) -> ProgressEvent | None:
    status = raw.get("status")
    if not isinstance(status, str):
        return None

    return ProgressEvent(
        request_id=request_id,
        status=status,
        percent=_calculate_percent(raw),
        speed=_format_speed(raw.get("speed")),
        eta=_as_int(raw.get("eta")),
        file_name=_file_name(raw.get("filename")),
    )


def _calculate_percent(raw: dict[str, Any]) -> float | None:
    downloaded = raw.get("downloaded_bytes")
    total = raw.get("total_bytes") or raw.get("total_bytes_estimate")
    if not isinstance(downloaded, (int, float)) or not isinstance(total, (int, float)):
        return None
    if total <= 0:
        return None
    return round(downloaded * 100 / total, 1)


def _format_speed(speed: object) -> str | None:
    if not isinstance(speed, (int, float)) or speed <= 0:
        return None
    if speed >= _BYTES_PER_MIB:
        return f"{speed / _BYTES_PER_MIB:.1f}MiB/s"
    return f"{speed / _BYTES_PER_KIB:.1f}KiB/s"


def _as_int(value: object) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    return int(value)


def _file_name(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(value).name
