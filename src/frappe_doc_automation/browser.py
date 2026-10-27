"""Screenshot capture from a user-provided allowlisted staging URL."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


def capture(config: Path, output: Path, storage_state: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright

    settings = json.loads(config.read_text(encoding="utf-8"))
    base = settings["base_url"].rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("A valid HTTPS base_url without embedded credentials is required")
    if not storage_state.is_file():
        raise ValueError("Authenticated browser storage state missing; create it locally, never commit it")
    output.mkdir(parents=True, exist_ok=True)
    outputs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(storage_state), viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page = context.new_page()
        for item in settings.get("screens", []):
            path = item["path"]
            name = item["name"]
            if not path.startswith("/") or path.startswith("//") or "\\" in path or "?" in path or "#" in path:
                raise ValueError(f"Invalid relative path: {path}")
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
                raise ValueError(f"Invalid screenshot name: {name}")
            url = base + path
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                if urlparse(page.url).hostname != parsed.hostname or "/login" in urlparse(page.url).path.lower():
                    raise RuntimeError(f"Authentication or host validation failed for {path}")
                if response and response.status >= 400:
                    raise RuntimeError(f"Page returned HTTP {response.status}: {path}")
                if page.locator("text=Insufficient Permission").count() or page.locator("text=Not Permitted").count():
                    raise RuntimeError(f"Permissions denied: {path}")
                for css in settings.get("redact_selectors", []):
                    page.locator(css).evaluate_all("els => els.forEach(el => el.style.visibility = 'hidden')")
                outfile = output / (name + ".png")
                page.screenshot(path=str(outfile), full_page=True, animations="disabled")
                outputs.append(outfile)
            except Exception:
                if not settings.get("allow_failure", False):
                    raise
        browser.close()
    return outputs
