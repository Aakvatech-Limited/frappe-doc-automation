from frappe_doc_automation.routes import discover_routes
from frappe_doc_automation.enrich import embed_screenshots


def test_routes():
    catalogue = {"apps": [{"name": "rsvp", "doctypes": [
        {"name": "Invitation", "istable": False},
        {"name": "Guest Row", "istable": True}],
        "reports": [{"name": "Guest Summary"}]}]}
    routes = discover_routes(catalogue)
    assert routes[1]["path"] == "/app/invitation"
    assert len(routes) == 3


def test_embed(tmp_path):
    catalogue = {"apps": [{"name": "rsvp", "doctypes": [
        {"name": "Invitation", "istable": False}]}]}
    doc = tmp_path / "rsvp-invitation.md"
    doc.write_text("# Invitation\n")
    image = tmp_path / "screenshots" / "manager" / "rsvp-invitation.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"PNG")
    embed_screenshots(catalogue, tmp_path, {"Manager": {"rsvp-invitation"}})
    assert "screenshots/manager/rsvp-invitation.png" in doc.read_text()
