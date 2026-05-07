import io
import json
from pathlib import Path

from yt_dlp.utils import DownloadError

from video_download_engine import cli
from video_download_engine.errors import ErrorCode
from video_download_engine.protocol import DownloadResult, ProgressEvent


def _json_lines(stdout: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_download_command_outputs_progress_and_completed_json(
    monkeypatch: object,
    tmp_path: Path,
) -> None:
    def fake_download(request: object, on_progress: object = None) -> DownloadResult:
        if callable(on_progress):
            on_progress(
                ProgressEvent(
                    request_id="req-1",
                    status="downloading",
                    percent=42.5,
                    file_name="video.mp4",
                )
            )
        return DownloadResult(file_path=tmp_path / "video.mp4", title="视频标题")

    monkeypatch.setattr(cli, "download_video", fake_download)
    args = cli._build_parser().parse_args(
        [
            "download",
            "--request-id",
            "req-1",
            "--url",
            "https://v.douyin.com/example/",
            "--output-dir",
            str(tmp_path),
        ]
    )
    stdout = io.StringIO()

    exit_code = cli._handle_download(args, stdout)

    assert exit_code == 0
    assert _json_lines(stdout) == [
        {
            "type": "progress",
            "requestId": "req-1",
            "status": "downloading",
            "percent": 42.5,
            "fileName": "video.mp4",
        },
        {
            "type": "completed",
            "requestId": "req-1",
            "filePath": str(tmp_path / "video.mp4"),
            "title": "视频标题",
        },
    ]


def test_download_command_outputs_failed_json_for_missing_url(tmp_path: Path) -> None:
    args = cli._build_parser().parse_args(
        ["download", "--request-id", "req-1", "--output-dir", str(tmp_path)]
    )
    stdout = io.StringIO()

    exit_code = cli._handle_download(args, stdout)
    payload = _json_lines(stdout)[0]

    assert exit_code == 1
    assert payload["type"] == "failed"
    assert payload["requestId"] == "req-1"
    assert payload["errorCode"] == ErrorCode.URL_EMPTY


def test_download_command_maps_yt_dlp_error_to_failed_json(monkeypatch: object, tmp_path: Path) -> None:
    def fake_download(request: object, on_progress: object = None) -> DownloadResult:
        raise DownloadError("boom")

    monkeypatch.setattr(cli, "download_video", fake_download)
    args = cli._build_parser().parse_args(
        [
            "download",
            "--request-id",
            "req-1",
            "--url",
            "https://v.douyin.com/example/",
            "--output-dir",
            str(tmp_path),
        ]
    )
    stdout = io.StringIO()

    exit_code = cli._handle_download(args, stdout)
    payload = _json_lines(stdout)[0]

    assert exit_code == 1
    assert payload["type"] == "failed"
    assert payload["errorCode"] == ErrorCode.DOWNLOAD_FAILED


def test_download_command_passes_browser_cookies(monkeypatch: object, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_download(request: object, on_progress: object = None) -> DownloadResult:
        captured["request"] = request
        return DownloadResult(file_path=tmp_path / "video.mp4")

    monkeypatch.setattr(cli, "download_video", fake_download)
    args = cli._build_parser().parse_args(
        [
            "download",
            "--request-id",
            "req-1",
            "--url",
            "https://v.douyin.com/example/",
            "--output-dir",
            str(tmp_path),
            "--cookies-from-browser",
            "edge",
        ]
    )
    stdout = io.StringIO()

    exit_code = cli._handle_download(args, stdout)

    assert exit_code == 0
    assert getattr(captured["request"], "cookies_from_browser") == "edge"
