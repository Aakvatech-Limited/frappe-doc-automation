from __future__ import annotations
import re
from pathlib import Path


def validate(output: Path) -> list[str]:
    errors = []
    for file in sorted(output.rglob("*.md")):
        text = file.read_text(encoding="utf-8")
        for link in re.findall(r"!?(?:\[[^\]]*\])\(([^)]+)\)", text):
            if link.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = (file.parent / link.split("#")[0]).resolve()
            if not target.is_relative_to(output.resolve()) or not target.exists():
                errors.append(f"{file}: broken or unsafe local link: {link}")
    return errors
