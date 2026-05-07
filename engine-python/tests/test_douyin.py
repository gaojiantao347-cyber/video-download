from pathlib import Path
from typing import Any

import pytest

from video_download_engine.douyin import (
    _browser_target_url,
    _build_file_name,
    _download_media,
    _extract_aweme_id,
    _extract_video_info,
    _safe_stem,
    _unique_file_path,
    is_douyin_url,
)
from video_download_engine.errors import EngineError


def test_is_douyin_url_accepts_douyin_domains() -> None:
    assert is_douyin_url("https://v.douyin.com/example/") is True
    assert is_douyin_url("https://www.iesdouyin.com/share/video/1") is True


def test_is_douyin_url_rejects_other_domains() -> None:
    assert is_douyin_url("https://notdouyin.com/video/1") is False
    assert is_douyin_url("not a url") is False


def test_extract_aweme_id_from_path_query_and_html() -> None:
    assert _extract_aweme_id("https://www.douyin.com/video/7633847281410062705") == "7633847281410062705"
    assert _extract_aweme_id("https://www.douyin.com/?modal_id=123") == "123"
    assert _extract_aweme_id("https://www.douyin.com/", '{"awemeId":"456"}') == "456"


def test_browser_target_url_normalizes_known_aweme_id() -> None:
    assert (
        _browser_target_url("https://www.douyin.com/jingxuan?modal_id=7632183372408211700")
        == "https://www.douyin.com/video/7632183372408211700"
    )
    assert _browser_target_url("https://v.douyin.com/example/") == "https://v.douyin.com/example/"


def test_extract_video_info_prefers_h264_url() -> None:
    aweme_id, title, play_url = _extract_video_info(
        {
            "aweme_detail": {
                "aweme_id": "123",
                "desc": "标题",
                "video": {
                    "play_addr_h264": {"url_list": ["https://video.test/h264.mp4"]},
                    "play_addr": {"url_list": ["https://video.test/fallback.mp4"]},
                },
            }
        }
    )

    assert aweme_id == "123"
    assert title == "标题"
    assert play_url == "https://video.test/h264.mp4"


def test_extract_video_info_falls_back_to_play_addr() -> None:
    assert _extract_video_info(
        {
            "aweme_detail": {
                "group_id": 123,
                "video": {
                    "play_addr": {"url_list": ["https://video.test/fallback.mp4"]},
                },
            }
        }
    ) == ("123", None, "https://video.test/fallback.mp4")


def test_extract_video_info_requires_video_url() -> None:
    with pytest.raises(EngineError):
        _extract_video_info({"aweme_detail": {"aweme_id": "123", "video": {}}})


def test_build_file_name_sanitizes_title() -> None:
    assert _safe_stem(' a<>:"/\\|?*\n b ') == "a b"
    assert _build_file_name(' a<>:"/\\|?*\n b ', "123") == "a b [123].mp4"
    assert _build_file_name("   ", "123") == "douyin-123 [123].mp4"


def test_unique_file_path_avoids_overwrite(tmp_path: Path) -> None:
    existing = tmp_path / "video.mp4"
    existing.write_text("old", encoding="utf-8")

    assert _unique_file_path(tmp_path, "video.mp4") == tmp_path / "video (1).mp4"


def test_download_media_writes_file_and_reports_progress(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeResponse:
        headers = {"Content-Length": "6"}

        def __init__(self) -> None:
            self.chunks = [b"abc", b"def", b""]

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

        def read(self, size: int) -> bytes:
            return self.chunks.pop(0)

    def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
        assert request.full_url == "https://video.test/a.mp4"
        assert timeout == 60
        return FakeResponse()

    monkeypatch.setattr("video_download_engine.douyin.urlopen", fake_urlopen)
    events = []
    file_path = tmp_path / "video.mp4"

    _download_media("https://video.test/a.mp4", file_path, "https://www.douyin.com/video/1", "req-1", events.append)

    assert file_path.read_bytes() == b"abcdef"
    assert [event.status for event in events] == ["downloading", "downloading", "finished"]
    assert [event.percent for event in events] == [50.0, 100.0, 100.0]
