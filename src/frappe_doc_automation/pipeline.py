"""Optional end-to-end orchestration for documentation, captures and draft PRs."""
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from .discovery import discover
from .render import write_docs, slug
from .routes import discover_routes
from .enrich import embed_screenshots
from .ai import write_draft
from .browser import capture
from .validate import validate


def run(repo: Path, output: Path, config: Path | None = None,
        ai: bool = False, pr: bool = False, dry_run: bool = False) -> dict:
    catalogue = discover(repo)
    settings = json.loads(config.read_text(encoding="utf-8")) if config else {}
    routes = discover_routes(catalogue, settings.get("max_pages", 100))
    if dry_run:
        return {"routes": routes, "roles": [x["name"] for x in settings.get("roles", [])]}
    try:
        commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    output.mkdir(parents=True, exist_ok=True)
    write_docs(catalogue, output, commit)
    (output / "routes.json").write_text(json.dumps(routes, indent=2) + "\n", encoding="utf-8")
    captures = {}
    for role in settings.get("roles", []):
        state = Path(role["storage_state"]).expanduser()
        if not state.is_file():
            raise ValueError("Missing storage state for " + role["name"])
        role_name = slug(role["name"])
        role_config = output / (".capture-" + role_name + ".json")
        try:
            role_config.write_text(json.dumps({
                "base_url": settings["base_url"],
                "screens": routes,
                "redact_selectors": settings.get("redact_selectors", []),
                "allow_failure": True,
            }), encoding="utf-8")
            result = capture(role_config, output / "screenshots" / role_name, state)
            captures[role["name"]] = {p.stem for p in result}
        finally:
            role_config.unlink(missing_ok=True)
    embed_screenshots(catalogue, output, captures)
    ai_written = write_draft(catalogue, output, settings.get("ai_model", "gpt-4.1-mini")) if ai else False
    problems = validate(output)
    if problems:
        raise ValueError("Invalid documentation links: " + "; ".join(problems))
    if pr:
        publish(output, settings)
    return {"apps": len(catalogue["apps"]), "screenshots": {k: len(v) for k,v in captures.items()}, "ai_draft": ai_written}


def publish(output: Path, settings: dict) -> None:
    """GitHub CLI must already be authenticated with push access."""
    target = settings.get("target_repo")
    if not target or "/" not in target:
        raise ValueError("Configure target_repo as owner/repository")
    branch = settings.get("documentation_branch", "docs/automated-frappe-guide")
    with tempfile.TemporaryDirectory() as directory:
        working = Path(directory) / "repo"
        subprocess.run(["gh", "repo", "clone", target, str(working)], check=True)
        subprocess.run(["git", "-C", str(working), "checkout", "-b", branch], check=True)
        destination = working / "docs" / "generated"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(output, destination, ignore=shutil.ignore_patterns(".capture-*"))
        subprocess.run(["git", "-C", str(working), "add", "docs/generated"], check=True)
        if subprocess.run(["git", "-C", str(working), "diff", "--cached", "--quiet"]).returncode == 0:
            return
        subprocess.run(["git", "-C", str(working), "commit", "-m", "docs: generate Frappe app guide"], check=True)
        subprocess.run(["git", "-C", str(working), "push", "-u", "origin", branch], check=True)
        subprocess.run(["gh", "pr", "create", "-R", target, "--head", branch,
                        "--title", "docs: refresh Frappe application guide",
                        "--body", "Generated documentation. Review screenshots and AI drafts before merge."], check=True)
