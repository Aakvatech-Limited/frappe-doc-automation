from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from .browser import capture
from .discovery import discover
from .render import write_docs
from .validate import validate


def main() -> None:
    parser = argparse.ArgumentParser(prog="frappe-docs")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Discover Frappe metadata and generate Markdown")
    build.add_argument("--repo", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    shots = sub.add_parser("screenshots", help="Capture configured staging-site screens")
    shots.add_argument("--config", type=Path, required=True)
    shots.add_argument("--output", type=Path, required=True)
    shots.add_argument("--storage-state", type=Path, required=True)
    check = sub.add_parser("validate", help="Verify local Markdown links")
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        cat = discover(args.repo)
        try:
            sha = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            sha = "unknown"
        paths = write_docs(cat, args.output, sha)
        print(json.dumps({"generated": len(paths), "apps": len(cat["apps"])}))
    elif args.command == "screenshots":
        paths = capture(args.config, args.output, args.storage_state)
        print(json.dumps({"screenshots": [str(p) for p in paths]}))
    else:
        errors = validate(args.output)
        for e in errors:
            print(e)
        if errors:
            raise SystemExit(1)
        print("Markdown links valid")

if __name__ == "__main__":
    main()
