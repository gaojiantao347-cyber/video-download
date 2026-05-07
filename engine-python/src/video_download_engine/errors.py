from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp.utils import DownloadError, ExtractorError


class ErrorCode:
    URL_EMPTY = "URL_EMPTY"
    URL_INVALID = "URL_INVALID"
    OUTPUT_DIR_INVALID = "OUTPUT_DIR_INVALID"
    COOKIES_FILE_INVALID = "COOKIES_FILE_INVALID"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class EngineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ValidationError(EngineError):
    pass


def validate_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValidationError(ErrorCode.URL_EMPTY, "链接不能为空")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(ErrorCode.URL_INVALID, "链接必须是有效的 HTTP(S) 地址")
    return normalized


def ensure_output_dir(output_dir: Path) -> Path:
    if not str(output_dir).strip():
        raise ValidationError(ErrorCode.OUTPUT_DIR_INVALID, "下载目录不能为空")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValidationError(ErrorCode.OUTPUT_DIR_INVALID, f"下载目录不可用：{exc}") from exc

    if not output_dir.is_dir():
        raise ValidationError(ErrorCode.OUTPUT_DIR_INVALID, "下载目录不是文件夹")
    if not os.access(output_dir, os.W_OK):
        raise ValidationError(ErrorCode.OUTPUT_DIR_INVALID, "下载目录不可写")
    return output_dir


def ensure_cookies_file(cookies_file: Path | None) -> Path | None:
    if cookies_file is None:
        return None
    if not cookies_file.is_file():
        raise ValidationError(ErrorCode.COOKIES_FILE_INVALID, "Cookie 文件不存在或不是普通文件")
    return cookies_file


def to_engine_error(exc: Exception) -> EngineError:
    if isinstance(exc, EngineError):
        return exc
    if isinstance(exc, (DownloadError, ExtractorError)):
        return EngineError(ErrorCode.DOWNLOAD_FAILED, _download_error_message(str(exc)))
    return EngineError(ErrorCode.UNKNOWN_ERROR, f"未知错误：{exc}")


def _download_error_message(message: str) -> str:
    lower_message = message.lower()
    if "fresh cookies" in lower_message:
        return "下载失败：抖音需要新鲜 Cookie，请先用所选浏览器打开抖音后重试"
    if "dpapi" in lower_message and "decrypt" in lower_message:
        return "读取浏览器 Cookie 失败：Windows DPAPI 解密失败，请改用 Cookie 文件，或不选择浏览器 Cookie 后重试"
    if "could not copy chrome cookie database" in lower_message:
        return "读取浏览器 Cookie 失败：请关闭 Chrome 或 Edge 后重试，或改用 Cookie 文件"
    if "could not find" in lower_message and "cookies database" in lower_message:
        return "读取浏览器 Cookie 失败：未找到所选浏览器的 Cookie 数据库"
    return "下载失败：平台解析失败或链接不可访问"
