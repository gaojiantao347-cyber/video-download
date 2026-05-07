from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from video_download_engine.errors import EngineError, ErrorCode
from video_download_engine.progress import build_progress_event
from video_download_engine.protocol import DownloadResult, ProgressEvent

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
_DETAIL_PATH = "/aweme/v1/web/aweme/detail/"
_DOUYIN_DOMAINS = ("douyin.com", "iesdouyin.com")
_INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_SPACE_CHARS = re.compile(r"\s+")
_AWEME_ID_RE = re.compile(r"(?:/video/|/share/video/|/note/)(\d+)")


def is_douyin_url(url: str) -> bool:
    hostname = urlparse(url.strip()).hostname
    if not hostname:
        return False
    hostname = hostname.lower()
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in _DOUYIN_DOMAINS)


def download_douyin_video(
    url: str,
    output_dir: Path,
    request_id: str,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> DownloadResult:
    detail, referer = _fetch_aweme_detail(url)
    aweme_id, title, play_url = _extract_video_info(detail)
    file_path = _unique_file_path(output_dir, _build_file_name(title, aweme_id))
    _download_media(play_url, file_path, referer, request_id, on_progress)
    return DownloadResult(file_path=file_path, title=title)


def _fetch_aweme_detail(url: str) -> tuple[dict[str, Any], str]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音浏览器辅助解析不可用：缺少 Playwright 依赖") from exc

    target_url = _browser_target_url(url)
    last_error: Exception | None = None
    for channel in ("msedge", "chrome"):
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel=channel, headless=True)
                try:
                    context = browser.new_context(
                        user_agent=_USER_AGENT,
                        locale="zh-CN",
                        viewport={"width": 1920, "height": 1080},
                    )
                    page = context.new_page()
                    with page.expect_response(_is_detail_response, timeout=45_000) as response_info:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=45_000)
                    response = response_info.value
                    data = response.json()
                    if not isinstance(data, dict):
                        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音自动解析失败：详情接口返回格式异常")
                    return data, page.url
                finally:
                    browser.close()
        except EngineError:
            raise
        except (PlaywrightTimeoutError, PlaywrightError, Exception) as exc:
            last_error = exc
            continue

    raise EngineError(ErrorCode.DOWNLOAD_FAILED, f"抖音自动解析失败：无法启动或驱动本机浏览器：{last_error}")


def _browser_target_url(url: str) -> str:
    aweme_id = _extract_aweme_id(url)
    if aweme_id:
        return f"https://www.douyin.com/video/{aweme_id}"
    return url


def _is_detail_response(response: object) -> bool:
    url = getattr(response, "url", "")
    status = getattr(response, "status", 0)
    return isinstance(url, str) and _DETAIL_PATH in url and status == 200


def _extract_video_info(detail: dict[str, Any]) -> tuple[str, str | None, str]:
    aweme = detail.get("aweme_detail")
    if not isinstance(aweme, dict):
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音自动解析失败：详情接口未返回视频信息")

    aweme_id = _as_text(aweme.get("aweme_id")) or _as_text(aweme.get("group_id"))
    if not aweme_id:
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音自动解析失败：未找到视频 ID")

    title = _as_text(aweme.get("desc"))
    video = aweme.get("video")
    if not isinstance(video, dict):
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音自动解析失败：未找到视频播放信息")

    play_url = _first_url(video.get("play_addr_h264")) or _first_url(video.get("play_addr"))
    if not play_url:
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, "抖音自动解析失败：未找到可下载视频地址")

    return aweme_id, title, play_url


def _first_url(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    urls = value.get("url_list")
    if not isinstance(urls, list):
        return None
    for item in urls:
        if isinstance(item, str) and item.startswith(("http://", "https://")):
            return item
    return None


def _download_media(
    url: str,
    file_path: Path,
    referer: str,
    request_id: str,
    on_progress: Callable[[ProgressEvent], None] | None,
) -> None:
    request = Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Referer": referer,
            "Accept": "video/mp4,video/*,*/*;q=0.8",
        },
    )

    try:
        with urlopen(request, timeout=60) as response:
            total = _as_int(response.headers.get("Content-Length"))
            downloaded = 0
            with file_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    _emit_progress(request_id, file_path, downloaded, total, on_progress)
        _emit_finished(request_id, file_path, total, on_progress)
    except OSError as exc:
        raise EngineError(ErrorCode.DOWNLOAD_FAILED, f"抖音视频下载失败：{exc}") from exc


def _emit_progress(
    request_id: str,
    file_path: Path,
    downloaded: int,
    total: int | None,
    on_progress: Callable[[ProgressEvent], None] | None,
) -> None:
    if on_progress is None:
        return
    raw: dict[str, Any] = {
        "status": "downloading",
        "downloaded_bytes": downloaded,
        "filename": str(file_path),
    }
    if total is not None:
        raw["total_bytes"] = total
    event = build_progress_event(request_id, raw)
    if event is not None:
        on_progress(event)


def _emit_finished(
    request_id: str,
    file_path: Path,
    total: int | None,
    on_progress: Callable[[ProgressEvent], None] | None,
) -> None:
    if on_progress is None:
        return
    raw: dict[str, Any] = {
        "status": "finished",
        "filename": str(file_path),
    }
    if total is not None:
        raw["downloaded_bytes"] = total
        raw["total_bytes"] = total
    event = build_progress_event(request_id, raw)
    if event is not None:
        on_progress(event)


def _build_file_name(title: str | None, aweme_id: str) -> str:
    stem = _safe_stem(title) or f"douyin-{aweme_id}"
    return f"{stem} [{aweme_id}].mp4"


def _safe_stem(value: str | None) -> str | None:
    if not value:
        return None
    sanitized = _INVALID_FILE_CHARS.sub(" ", value)
    sanitized = _SPACE_CHARS.sub(" ", sanitized).strip(" .")
    if not sanitized:
        return None
    return sanitized[:120].strip(" .") or None


def _unique_file_path(output_dir: Path, file_name: str) -> Path:
    candidate = output_dir / file_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        next_candidate = output_dir / f"{stem} ({index}){suffix}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def _as_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, int):
        return str(value)
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _extract_aweme_id(url: str, html: str = "") -> str | None:
    parsed = urlparse(url)
    match = _AWEME_ID_RE.search(parsed.path)
    if match:
        return match.group(1)

    query = parse_qs(parsed.query)
    for key in ("aweme_id", "modal_id", "item_id"):
        values = query.get(key)
        if values and values[0].isdigit():
            return values[0]

    for pattern in (r'"awemeId"\s*:\s*"?(\d+)"?', r'"aweme_id"\s*:\s*"?(\d+)"?', r'"modal_id"\s*:\s*"?(\d+)"?'):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None
