"""Render truthful Markdown: no unsupported claims about behavior."""
from __future__ import annotations

import json
import re
from pathlib import Path


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or "item"


def escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("`", "\\`")


def write_docs(catalogue: dict, output: Path, commit: str = "unknown") -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    (output / "catalogue.json").write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files.append(output / "catalogue.json")
    index = ["# Frappe Application Documentation", "", f"Source commit: `{escape(commit)}`", "",
             "Generated from repository metadata. UI behavior and permissions require running-site verification.", ""]
    for app in catalogue["apps"]:
        index += [f"## {escape(app['name'])}", "", "### Modules", ""]
        index += [f"- {escape(m)}" for m in app["modules"]] or ["- No modules declared"]
        index += ["", "### DocTypes", ""]
        for dt in app["doctypes"]:
            if dt["istable"]:
                continue
            name = f"{slug(app['name'])}-{slug(dt['name'])}.md"
            index.append(f"- [{escape(dt['name'])}]({name})")
            lines = [f"# {escape(dt['name'])}", "", f"App: **{escape(app['name'])}**  ",
                     f"Module: **{escape(dt['module'])}**  ", f"Source: `{dt['source']}`  ",
                     f"Submittable: **{'Yes' if dt['is_submittable'] else 'No'}**", "",
                     "> Generated from DocType metadata. Validate actual behavior and visibility on a test site.", "",
                     "## Fields", "", "| Label | Fieldname | Type | Required | Read-only |", "|---|---|---|---|---|"]
            for f in dt["fields"]:
                lines.append(f"| {escape(f['label'])} | `{escape(f['fieldname'])}` | {escape(f['fieldtype'])} | {'Yes' if f['reqd'] else 'No'} | {'Yes' if f['read_only'] else 'No'} |")
            lines += ["", "## User procedure", "", "Pending browser verification and editorial review.", ""]
            path = output / name
            path.write_text("\n".join(lines), encoding="utf-8")
            files.append(path)
        index += ["", "### Reports", ""]
        index += [f"- {escape(r['name'])} ({escape(r['report_type'])}) — `{r['source']}`" for r in app["reports"]] or ["- None discovered"]
        index += ["", "### Workflows", ""]
        index += [f"- {escape(w['name'])}: {', '.join(map(escape, w['states']))} — `{w['source']}`" for w in app["workflows"]] or ["- None discovered"]
        index.append("")
    file = output / "index.md"
    file.write_text("\n".join(index), encoding="utf-8")
    files.append(file)
    return files
