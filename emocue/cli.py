"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import create_backend
from .parser import parse_script
from .render import render_script

DEMO_SCRIPT = """\
# EmoCue demo: no GPU, no model, just tones.
[whisper:0.9] 靠近一点，别出声。
[pause:0.6]
[happy:0.8] 今天的花，开得很好。
[sigh:0.5] 只是有点累。
[laugh:0.9] 算了，不想了。
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emocue",
        description="Turn emotion-tagged scripts into segmented TTS audio, cues, and Cubase markers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="parse a script and print the segments as JSON")
    parse_cmd.add_argument("script", type=Path)

    render_cmd = subparsers.add_parser("render", help="render a script to audio + cue sheets")
    render_cmd.add_argument("script", type=Path)
    render_cmd.add_argument("--out", type=Path, default=Path("out"))
    render_cmd.add_argument("--backend", choices=["sapi", "mock", "http", "command"], default="sapi")
    render_cmd.add_argument("--url", default="http://127.0.0.1:8000/tts")
    render_cmd.add_argument("--api-key", default=None)
    render_cmd.add_argument("--command", default=None, dest="command_template")
    render_cmd.add_argument("--gap", type=float, default=0.25)
    render_cmd.add_argument("--sample-rate", type=int, default=24000)
    render_cmd.add_argument("--language", default="ja")
    render_cmd.add_argument("--timeout", type=float, default=120.0)
    render_cmd.add_argument("--json", action="store_true", dest="as_json")

    demo_cmd = subparsers.add_parser("demo", help="render a built-in demo with the SAPI backend")
    demo_cmd.add_argument("--out", type=Path, default=Path("demo_out"))
    demo_cmd.add_argument("--gap", type=float, default=0.25)
    demo_cmd.add_argument("--mock", action="store_true", help="use tones instead of Windows SAPI")

    return parser


def _print_result(result, as_json: bool) -> None:
    payload = {
        "out_dir": str(result.out_dir),
        "full_wav": str(result.full_wav),
        "cues_csv": str(result.cues_csv),
        "cues_mid": str(result.cues_mid),
        "project_json": str(result.project_json),
        "sample_rate": result.sample_rate,
        "total_duration": round(result.total_duration, 3),
        "segments": len(result.cues),
        "warnings": result.warnings,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"full.wav     {result.full_wav}")
    print(f"cues.csv     {result.cues_csv}")
    print(f"cues.mid     {result.cues_mid}")
    print(f"project.json {result.project_json}")
    print(f"segments     {len(result.cues)}")
    print(f"duration     {result.total_duration:.2f}s @ {result.sample_rate} Hz")
    for warning in result.warnings:
        print(f"warning: {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "parse":
        text = args.script.read_text(encoding="utf-8")
        script = parse_script(text)
        print(
            json.dumps(
                {
                    "segments": [
                        {
                            "index": segment.index,
                            "text": segment.text,
                            "emotion": segment.emotion,
                            "intensity": segment.intensity,
                            "pause": segment.pause,
                            "kind": segment.kind,
                            "line": segment.line,
                        }
                        for segment in script.segments
                    ],
                    "warnings": script.warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "demo":
        script = parse_script(DEMO_SCRIPT)
        backend = create_backend("mock" if args.mock else "sapi")
        result = render_script(script, backend, args.out, gap=args.gap)
        _print_result(result, as_json=False)
        return 0

    if args.command == "render":
        text = args.script.read_text(encoding="utf-8")
        script = parse_script(text)
        backend = create_backend(
            args.backend,
            url=args.url,
            api_key=args.api_key,
            template=args.command_template,
            timeout=args.timeout,
        )
        result = render_script(
            script,
            backend,
            args.out,
            gap=args.gap,
            sample_rate=args.sample_rate,
            language=args.language,
        )
        _print_result(result, as_json=args.as_json)
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
