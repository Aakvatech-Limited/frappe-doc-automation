"""Static, evidence-based discovery without executing source repository code."""
from __future__ import annotations

import json
from pathlib import Path


def discover(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")
    apps = []
    for hooks in sorted(root.rglob("hooks.py")):
        if any(p in {".git", ".venv", "node_modules", "env", "sites"} for p in hooks.parts):
            continue
        if not (hooks.parent / "modules.txt").exists():
            continue
        app = hooks.parent.name
        modules = [s.strip() for s in (hooks.parent / "modules.txt").read_text(encoding="utf-8").splitlines() if s.strip()]
        doctypes = []
        for file in sorted(hooks.parent.rglob("doctype/*/*.json")):
            if any(x in file.parts for x in ("node_modules", ".git")):
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError):
                continue
            if data.get("doctype") != "DocType" and not (data.get("fields") and data.get("name")):
                continue
            doctypes.append({
                "name": data.get("name", file.stem), "module": data.get("module", ""),
                "is_submittable": bool(data.get("is_submittable")),
                "istable": bool(data.get("istable")),
                "fields": [{"label": f.get("label", ""), "fieldname": f.get("fieldname", ""),
                            "fieldtype": f.get("fieldtype", ""), "options": f.get("options", ""),
                            "reqd": bool(f.get("reqd")), "read_only": bool(f.get("read_only"))}
                           for f in data.get("fields", []) if f.get("fieldname")],
                "source": file.relative_to(root).as_posix(),
            })
        reports = []
        for file in sorted(hooks.parent.rglob("report/*/*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError):
                continue
            if data.get("report_name") or data.get("doctype") == "Report":
                reports.append({"name": data.get("report_name", file.stem),
                                "ref_doctype": data.get("ref_doctype", ""),
                                "report_type": data.get("report_type", ""),
                                "source": file.relative_to(root).as_posix()})
        workflows = []
        for file in sorted(hooks.parent.rglob("workflow/*/*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError):
                continue
            if data.get("workflow_name") or data.get("doctype") == "Workflow":
                workflows.append({"name": data.get("workflow_name", file.stem),
                                  "document_type": data.get("document_type", ""),
                                  "states": [x.get("state", "") for x in data.get("states", [])],
                                  "source": file.relative_to(root).as_posix()})
        apps.append({"name": app, "modules": modules, "doctypes": doctypes,
                     "reports": reports, "workflows": workflows,
                     "source": hooks.relative_to(root).as_posix()})
    if not apps:
        raise ValueError("No Frappe app discovered (expected hooks.py and modules.txt in an app package)")
    return {"schema_version": 1, "apps": apps}
