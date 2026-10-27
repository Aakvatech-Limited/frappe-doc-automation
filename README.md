# Aakvatech Frappe Documentation Automation

Evidence-backed Markdown generation and opt-in Playwright screenshots for Frappe and ERPNext applications. Markdown remains the authoritative source for a future Frappe Docs-inspired portal.

## Features (v0.1)

- Discover Frappe app packages using `hooks.py` and `modules.txt`.
- Extract DocTypes, field definitions, submittable flags, reports, and workflow state names without executing the app.
- Generate deterministic Markdown pages and a JSON feature catalogue with source paths and Git SHA.
- Capture explicitly configured screens using authenticated Playwright sessions on an HTTPS staging site.
- Validate Markdown links and run pytest through GitHub Actions.

## Installation

```bash
python -m pip install -e '.[test]'
frappe-docs build --repo /path/to/frappe-app --output ./generated-docs
frappe-docs validate --output ./generated-docs
```

For screenshots, install `.[browser]` and Chromium through `python -m playwright install chromium`, then run:

```bash
frappe-docs screenshots --config examples/screenshots.example.json --storage-state /secure/storage-state.json --output ./generated-docs/screenshots
```

**Security:** Only use sanitized staging data and least-privileged test accounts. Do not commit session states, passwords, customer information, or unreviewed screenshots. Restrict browser egress to trusted hosts.

## Planned extensions

Role-aware UI traversal, custom-script analysis, AI-authored procedural documentation with review flags, screenshot annotation and privacy verification, change detection, documentation PR generation, and a versioned Frappe Docs-style portal.

This foundation does **not** automatically infer application business behavior, create role-specific screenshots, open PRs in target apps, or deploy a website. These require separate development and validation.
