from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DownloadRequest:
    request_id: str
    url: str
    output_dir: Path
    remove_watermark: bool = True
    allow_fallback: bool = True
    cookies_file: Path | None = None
    cookies_from_browser: str | None = None


@dataclass(frozen=True)
class DownloadResult:
    file_path: Path
    title: str | None = None


@dataclass(frozen=True)
class CompletedEvent:
    request_id: str
    file_path: Path
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": "completed",
            "requestId": self.request_id,
            "filePath": str(self.file_path),
        }
        if self.title:
            result["title"] = self.title
        return result


@dataclass(frozen=True)
class FailedEvent:
    request_id: str
    error_code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "failed",
            "requestId": self.request_id,
            "errorCode": self.error_code,
            "message": self.message,
        }


@dataclass(frozen=True)
class ProgressEvent:
    request_id: str
    status: str
    percent: float | None = None
    speed: str | None = None
    eta: int | None = None
    file_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": "progress",
            "requestId": self.request_id,
            "status": self.status,
        }
        if self.percent is not None:
            result["percent"] = self.percent
        if self.speed:
            result["speed"] = self.speed
        if self.eta is not None:
            result["eta"] = self.eta
        if self.file_name:
            result["fileName"] = self.file_name
        return result
