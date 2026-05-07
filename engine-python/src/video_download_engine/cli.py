from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO
from uuid import uuid4

from video_download_engine.downloader import download_video
from video_download_engine.errors import EngineError, to_engine_error
from video_download_engine.protocol import CompletedEvent, DownloadRequest, FailedEvent, ProgressEvent


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        return _handle_download(args)

    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-download-engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download one public video URL")
    download.add_argument("--request-id", default=None)
    download.add_argument("--url", default="")
    download.add_argument("--output-dir", default="")
    download.add_argument("--remove-watermark", dest="remove_watermark", action="store_true", default=True)
    download.add_argument("--no-remove-watermark", dest="remove_watermark", action="store_false")
    download.add_argument("--allow-fallback", dest="allow_fallback", action="store_true", default=True)
    download.add_argument("--no-allow-fallback", dest="allow_fallback", action="store_false")
    download.add_argument("--cookies-file", default=None)
    download.add_argument("--cookies-from-browser", default=None)
    return parser


def _handle_download(args: argparse.Namespace, stdout: TextIO | None = None) -> int:
    output = stdout if stdout is not None else sys.stdout
    request_id = args.request_id or str(uuid4())

    try:
        request = DownloadRequest(
            request_id=request_id,
            url=args.url,
            output_dir=Path(args.output_dir),
            remove_watermark=args.remove_watermark,
            allow_fallback=args.allow_fallback,
            cookies_file=Path(args.cookies_file) if args.cookies_file else None,
            cookies_from_browser=args.cookies_from_browser,
        )

        def emit_progress(event: ProgressEvent) -> None:
            _print_json(event.to_dict(), output)

        result = download_video(request, on_progress=emit_progress)
        _print_json(
            CompletedEvent(
                request_id=request.request_id,
                file_path=result.file_path,
                title=result.title,
            ).to_dict(),
            output,
        )
        return 0
    except EngineError as exc:
        _print_failure(request_id, exc, output)
        return 1
    except Exception as exc:
        _print_failure(request_id, to_engine_error(exc), output)
        return 1


def _print_failure(request_id: str, exc: EngineError, output: TextIO) -> None:
    _print_json(
        FailedEvent(
            request_id=request_id,
            error_code=exc.code,
            message=exc.message,
        ).to_dict(),
        output,
    )


def _print_json(payload: dict[str, object], output: TextIO) -> None:
    print(json.dumps(payload), file=output, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
