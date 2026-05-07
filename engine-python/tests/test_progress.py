from video_download_engine.progress import build_progress_event


def test_build_progress_event_converts_yt_dlp_status() -> None:
    event = build_progress_event(
        "req-1",
        {
            "status": "downloading",
            "downloaded_bytes": 512,
            "total_bytes": 1024,
            "speed": 1024 * 1024,
            "eta": 12.8,
            "filename": "D:/Videos/video.mp4",
        },
    )

    assert event is not None
    assert event.to_dict() == {
        "type": "progress",
        "requestId": "req-1",
        "status": "downloading",
        "percent": 50.0,
        "speed": "1.0MiB/s",
        "eta": 12,
        "fileName": "video.mp4",
    }
