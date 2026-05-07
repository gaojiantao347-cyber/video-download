from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError

from video_download_engine.errors import (
    ErrorCode,
    ValidationError,
    ensure_output_dir,
    to_engine_error,
    validate_url,
)


def test_validate_url_accepts_http_url() -> None:
    assert validate_url(" https://v.douyin.com/example/ ") == "https://v.douyin.com/example/"


def test_validate_url_rejects_empty_url() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_url("  ")

    assert exc_info.value.code == ErrorCode.URL_EMPTY


def test_validate_url_rejects_non_http_url() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_url("file:///tmp/video.mp4")

    assert exc_info.value.code == ErrorCode.URL_INVALID


def test_ensure_output_dir_rejects_regular_file(tmp_path: Path) -> None:
    regular_file = tmp_path / "download.txt"
    regular_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValidationError) as exc_info:
        ensure_output_dir(regular_file)

    assert exc_info.value.code == ErrorCode.OUTPUT_DIR_INVALID


def test_to_engine_error_maps_yt_dlp_download_error() -> None:
    error = to_engine_error(DownloadError("boom"))

    assert error.code == ErrorCode.DOWNLOAD_FAILED
    assert "下载失败" in error.message


def test_to_engine_error_explains_fresh_cookie_requirement() -> None:
    error = to_engine_error(DownloadError("Fresh cookies (not necessarily logged in) are needed"))

    assert error.code == ErrorCode.DOWNLOAD_FAILED
    assert "新鲜 Cookie" in error.message


def test_to_engine_error_explains_locked_browser_cookie_database() -> None:
    error = to_engine_error(DownloadError("Could not copy Chrome cookie database"))

    assert error.code == ErrorCode.DOWNLOAD_FAILED
    assert "关闭 Chrome 或 Edge" in error.message


def test_to_engine_error_explains_dpapi_cookie_decrypt_failure() -> None:
    error = to_engine_error(DownloadError("Failed to decrypt with DPAPI"))

    assert error.code == ErrorCode.DOWNLOAD_FAILED
    assert "DPAPI 解密失败" in error.message
