from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from .browser import capture
from .discovery import discover
from .render import write_docs
from .validate import validate
from .pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(prog="frappe-docs")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Generate metadata-based Markdown")
    build.add_argument("--repo", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    shots = sub.add_parser("screenshots", help="Capture configured staging-site screens")
    shots.add_argument("--config", type=Path, required=True)
    shots.add_argument("--output", type=Path, required=True)
    shots.add_argument("--storage-state", type=Path, required=True)
    check = sub.add_parser("validate", help="Validate Markdown links")
    check.add_argument("--output", type=Path, required=True)
    pipe = sub.add_parser("pipeline", help="Generate, capture, and optionally publish")
    pipe.add_argument("--repo", type=Path, required=True)
    pipe.add_argument("--output", type=Path, required=True)
    pipe.add_argument("--config", type=Path)
    pipe.add_argument("--ai", action="store_true")
    pipe.add_argument("--pr", action="store_true")
    pipe.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        catalogue = discover(args.repo)
        try:
            sha = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"],
                                          text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            sha = "unknown"
        files = write_docs(catalogue, args.output, sha)
        print(json.dumps({"generated": len(files), "apps": len(catalogue["apps"])}))
    elif args.command == "screenshots":
        files = capture(args.config, args.output, args.storage_state)
        print(json.dumps({"screenshots": [str(p) for p in files]}))
    elif args.command == "pipeline":
        print(json.dumps(run(args.repo, args.output, args.config, args.ai, args.pr, args.dry_run), indent=2))
    else:
        errors = validate(args.output)
        for error in errors:
            print(error)
        if errors:
            raise SystemExit(1)
        print("Markdown links valid")


if __name__ == "__main__":
    main()
