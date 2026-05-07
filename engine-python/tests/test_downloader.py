from pathlib import Path
from typing import Any

import pytest
from yt_dlp.utils import DownloadError

from video_download_engine.downloader import download_video
from video_download_engine.protocol import DownloadRequest, DownloadResult


class FakeYoutubeDL:
    instances: list["FakeYoutubeDL"] = []

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options
        FakeYoutubeDL.instances.append(self)

    def __enter__(self) -> "FakeYoutubeDL":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def extract_info(self, url: str, download: bool) -> dict[str, Any]:
        assert url == "https://v.douyin.com/example/"
        assert download is True
        file_path = str(Path(self.options["paths"]["home"]) / "video.mp4")
        progress_hook = self.options["progress_hooks"][0]
        progress_hook(
            {
                "status": "downloading",
                "downloaded_bytes": 512,
                "total_bytes": 1024,
                "filename": file_path,
            }
        )
        progress_hook({"status": "finished", "filename": file_path})
        return {
            "id": "abc",
            "title": "视频标题",
            "ext": "mp4",
            "requested_downloads": [{"filepath": file_path}],
        }

    def prepare_filename(self, info: dict[str, Any]) -> str:
        return str(Path(self.options["paths"]["home"]) / "prepared.mp4")

    def sanitize_info(self, info: dict[str, Any]) -> dict[str, Any]:
        return info


class FailingYoutubeDL:
    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options

    def __enter__(self) -> "FailingYoutubeDL":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def extract_info(self, url: str, download: bool) -> dict[str, Any]:
        raise DownloadError("Fresh cookies (not necessarily logged in) are needed")


def test_download_video_uses_yt_dlp_and_returns_file_path(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FakeYoutubeDL)
    FakeYoutubeDL.instances.clear()

    result = download_video(
        DownloadRequest(
            request_id="req-1",
            url="https://v.douyin.com/example/",
            output_dir=tmp_path,
        )
    )

    assert result.file_path == tmp_path / "video.mp4"
    assert result.title == "视频标题"
    assert FakeYoutubeDL.instances[0].options["noplaylist"] is True
    assert FakeYoutubeDL.instances[0].options["paths"] == {"home": str(tmp_path)}


def test_download_video_reports_progress(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FakeYoutubeDL)
    FakeYoutubeDL.instances.clear()
    events = []

    download_video(
        DownloadRequest(
            request_id="req-1",
            url="https://v.douyin.com/example/",
            output_dir=tmp_path,
        ),
        on_progress=events.append,
    )

    assert events[0].to_dict() == {
        "type": "progress",
        "requestId": "req-1",
        "status": "downloading",
        "percent": 50.0,
        "fileName": "video.mp4",
    }
    assert events[1].to_dict() == {
        "type": "progress",
        "requestId": "req-1",
        "status": "finished",
        "fileName": "video.mp4",
    }


def test_download_video_uses_browser_cookies(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FakeYoutubeDL)
    FakeYoutubeDL.instances.clear()

    download_video(
        DownloadRequest(
            request_id="req-1",
            url="https://v.douyin.com/example/",
            output_dir=tmp_path,
            cookies_from_browser="edge",
        )
    )

    assert FakeYoutubeDL.instances[0].options["cookiesfrombrowser"] == ("edge",)


def test_download_video_uses_douyin_fallback_when_yt_dlp_fails(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FailingYoutubeDL)
    called: dict[str, object] = {}

    def fake_download_douyin_video(url: str, output_dir: Path, request_id: str, on_progress: object) -> DownloadResult:
        called["url"] = url
        called["output_dir"] = output_dir
        called["request_id"] = request_id
        return DownloadResult(file_path=output_dir / "fallback.mp4", title="fallback")

    monkeypatch.setattr("video_download_engine.downloader.download_douyin_video", fake_download_douyin_video)

    result = download_video(
        DownloadRequest(
            request_id="req-1",
            url="https://v.douyin.com/example/",
            output_dir=tmp_path,
        )
    )

    assert result.file_path == tmp_path / "fallback.mp4"
    assert result.title == "fallback"
    assert called == {
        "url": "https://v.douyin.com/example/",
        "output_dir": tmp_path,
        "request_id": "req-1",
    }


def test_download_video_does_not_fallback_when_disabled(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FailingYoutubeDL)

    with pytest.raises(DownloadError):
        download_video(
            DownloadRequest(
                request_id="req-1",
                url="https://v.douyin.com/example/",
                output_dir=tmp_path,
                allow_fallback=False,
            )
        )


def test_download_video_does_not_fallback_for_non_douyin_url(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr("video_download_engine.downloader.YoutubeDL", FailingYoutubeDL)

    with pytest.raises(DownloadError):
        download_video(
            DownloadRequest(
                request_id="req-1",
                url="https://example.com/video/1",
                output_dir=tmp_path,
            )
        )
