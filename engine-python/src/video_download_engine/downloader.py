from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from video_download_engine.douyin import download_douyin_video, is_douyin_url
from video_download_engine.errors import EngineError, ErrorCode, ensure_cookies_file, ensure_output_dir, validate_url
from video_download_engine.progress import build_progress_event
from video_download_engine.protocol import DownloadRequest, DownloadResult, ProgressEvent

_DEFAULT_OUTPUT_TEMPLATE = "%(title).200B [%(id)s].%(ext)s"
_SUPPORTED_COOKIE_BROWSERS = {"edge", "chrome", "firefox"}


def download_video(
    request: DownloadRequest,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> DownloadResult:
    url = validate_url(request.url)
    output_dir = ensure_output_dir(request.output_dir)
    cookies_file = ensure_cookies_file(request.cookies_file)
    cookies_from_browser = _normalize_cookies_from_browser(request.cookies_from_browser)
    downloaded_file: dict[str, str] = {}

    def handle_progress(status: dict[str, Any]) -> None:
        if status.get("status") == "finished" and status.get("filename"):
            downloaded_file["path"] = str(status["filename"])

        if on_progress is None:
            return

        event = build_progress_event(request.request_id, status)
        if event is not None:
            on_progress(event)

    options: dict[str, Any] = {
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "paths": {"home": str(output_dir)},
        "outtmpl": {"default": _DEFAULT_OUTPUT_TEMPLATE},
        "progress_hooks": [handle_progress],
    }
    if cookies_file is not None:
        options["cookiefile"] = str(cookies_file)
    elif cookies_from_browser is not None:
        options["cookiesfrombrowser"] = (cookies_from_browser,)

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            if not isinstance(info, dict):
                raise RuntimeError("yt-dlp 未返回视频信息")

            prepared_file = ydl.prepare_filename(info)
            safe_info = ydl.sanitize_info(info)
    except (DownloadError, ExtractorError):
        if request.allow_fallback and is_douyin_url(url):
            return download_douyin_video(url, output_dir, request.request_id, on_progress)
        raise

    return DownloadResult(
        file_path=Path(_resolve_file_path(safe_info, downloaded_file.get("path"), prepared_file)),
        title=_as_text(safe_info.get("title")),
    )


def _normalize_cookies_from_browser(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    normalized = value.strip().lower()
    if normalized not in _SUPPORTED_COOKIE_BROWSERS:
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, f"不支持的浏览器 Cookie 来源：{value}")
    return normalized


def _resolve_file_path(info: dict[str, Any], captured: str | None, prepared: str | None) -> str:
    if captured:
        return captured

    requested_downloads = info.get("requested_downloads")
    if isinstance(requested_downloads, list):
        for item in requested_downloads:
            if not isinstance(item, dict):
                continue
            file_path = item.get("filepath") or item.get("_filename")
            if isinstance(file_path, str) and file_path:
                return file_path

    filename = info.get("_filename")
    if isinstance(filename, str) and filename:
        return filename

    if prepared:
        return prepared
    raise RuntimeError("无法确定下载后的文件路径")


def _as_text(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
