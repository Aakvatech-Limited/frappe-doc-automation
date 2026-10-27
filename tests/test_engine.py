import json
from pathlib import Path
import pytest
from frappe_doc_automation.discovery import discover
from frappe_doc_automation.render import write_docs
from frappe_doc_automation.validate import validate


def fixture(tmp_path):
    pkg = tmp_path / "rsvp" / "rsvp"
    (pkg / "rsvp" / "doctype" / "event").mkdir(parents=True)
    (pkg / "hooks.py").write_text("app_name='rsvp'\n")
    (pkg / "modules.txt").write_text("RSVP\n")
    d = {"doctype": "DocType", "name": "Event", "module": "RSVP", "is_submittable": 1,
         "fields": [{"label": "Event Name", "fieldname": "event_name", "fieldtype": "Data", "reqd": 1}]}
    (pkg / "rsvp" / "doctype" / "event" / "event.json").write_text(json.dumps(d))
    return tmp_path / "rsvp"


def test_discover_and_generate(tmp_path):
    repo = fixture(tmp_path)
    cat = discover(repo)
    assert cat["apps"][0]["doctypes"][0]["name"] == "Event"
    out = tmp_path / "docs"
    write_docs(cat, out, "abc123")
    assert "Event Name" in (out / "rsvp-event.md").read_text()
    assert validate(out) == []


def test_validate_broken_link(tmp_path):
    (tmp_path / "doc.md").write_text("[missing](missing.md)")
    assert validate(tmp_path)


def test_discover_missing(tmp_path):
    with pytest.raises(ValueError):
        discover(tmp_path)
