# User Guide: Generate Frappe App Documentation from Start to Finish

This walkthrough uses **Aakvatech-Limited/av_rsvp** as an example. It starts with a clean machine and ends with locally generated Markdown, optional live screenshots, an optional AI-assisted draft, a browsable documentation website, and an optional GitHub documentation pull request.

> **Current scope:** The tool generates a reference for discovered DocTypes and metadata, plus list/report screen captures when available. It does **not** automatically choose a safe sample Form record, verify all business actions, or publish a fully reviewed user manual. AI-generated text remains a draft requiring human review.

## 0. What you need

- A Linux/macOS machine, WSL2, or a suitable CI runner with **Python 3.10+**, Git, and network access to GitHub.
- Read access to the Frappe app repository you want to document.
- For screenshots only: a **sanitized Frappe staging site**, the app installed there, and a dedicated account for each role being documented.
- For AI drafting only: an OpenAI API key and approval to send repository **metadata** to the API.
- For automatic documentation PRs only: GitHub CLI (`gh`) authenticated with permission to push and open PRs in the **target app repository**.

The generator runs independently of the Frappe bench; do not install it as a Frappe app. **Never use a production session or capture confidential customer data.**

## 1. Download both repositories

Run these commands from a terminal:

```bash
mkdir -p ~/frappe-doc-pilot
cd ~/frappe-doc-pilot

git clone https://github.com/Aakvatech-Limited/frappe-doc-automation.git
git clone https://github.com/Aakvatech-Limited/av_rsvp.git

cd frappe-doc-automation
```

For private target repositories, authenticate Git before cloning. You can substitute any other Frappe app repository for `av_rsvp`.

The example workspace now looks like:

```text
~/frappe-doc-pilot/
├── frappe-doc-automation/       # documentation tool
└── av_rsvp/                     # source app to document
```

## 2. Install the tool and run its tests

On Linux/macOS/WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test,browser,site]'
python -m playwright install chromium
pytest -q
```

If your Linux machine is missing Chromium operating-system libraries, install the dependencies following Playwright's guidance (e.g. `python -m playwright install --with-deps chromium` on a supported Linux distribution).

**Expected result:** pytest completes without errors and `frappe-docs --help` lists `build`, `screenshots`, `validate`, and `pipeline`. A failing test means the environment or code needs investigation before the pilot continues.

## 3. Preview what the tool can discover (no browser needed)

From `~/frappe-doc-pilot/frappe-doc-automation`:

```bash
frappe-docs pipeline \
  --repo ../av_rsvp \
  --output ./generated-docs \
  --dry-run
```

The command prints JSON containing proposed routes, for example:

```json
{
  "routes": [
    {"name": "desk", "path": "/app"},
    {"name": "av-rsvp-example", "path": "/app/example", "doctype": "Example"}
  ],
  "roles": []
}
```

This is **illustrative**, not a claim that `av_rsvp` has an `Example` DocType. The actual routes depend on the repository contents. **Dry-run does not create documentation or capture screenshots.** Route discovery is inferred from naming conventions; some routes may need correction for the deployed site.

## 4. Generate actual Markdown and check it

```bash
frappe-docs pipeline \
  --repo ../av_rsvp \
  --output ./generated-docs

frappe-docs validate --output ./generated-docs
```

Alternatively, the existing metadata-only command remains available:

```bash
frappe-docs build --repo ../av_rsvp --output ./generated-docs
```

Open `generated-docs/index.md` in a Markdown viewer or editor. The output will include:

```text
generated-docs/
├── index.md                   # entry point and app/module index
├── catalogue.json             # source-derived machine-readable catalogue
├── routes.json                # proposed screens (pipeline command only)
└── <app>-<doctype>.md         # one page per non-child DocType
```

For each generated DocType page, inspect the module, source JSON path, submittable flag, and table of fields. Screenshots and procedural descriptions are **not yet present** unless subsequent steps are run. If nothing is discovered, verify the app is a Frappe app with `hooks.py` and `modules.txt` in its package and that `--repo` points to the correct directory.

## 5. Prepare a safe staging site for real screenshots

Use a separate Frappe v16 site with `av_rsvp` installed, safe demonstration records, and a dedicated non-administrator test account. Make sure the account can open the app's list and report routes. The screenshot tool does not create records or fill forms.

For the first test, **use one role**. Additional roles can be added later.

Create a local Playwright authentication-state file *outside* the documentation repository. The following script lets a human log in interactively.

Save as `~/frappe-doc-pilot/login.py`:

```python
from pathlib import Path
from playwright.sync_api import sync_playwright

site = "https://your-staging-site.example.com"
state = Path.home() / ".config/frappe-doc-pilot/manager-state.json"
state.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(site + "/login")
    input("Complete login in the opened browser, then press Enter here: ")
    if "/login" in page.url.lower():
        raise RuntimeError("Still on login page; authenticate before saving state")
    context.storage_state(path=str(state))
    browser.close()

state.chmod(0o600)
print(f"Saved protected session state to {state}")
```

Run:

```bash
python ~/frappe-doc-pilot/login.py
```

Set the site URL to your actual HTTPS staging hostname. This interactive approach needs a graphical desktop; for a headless runner, provision an approved authenticated state through your organization's secure secret-management process. Treat the JSON as a password: keep it out of Git, logs, public build artifacts, and shared computers. These session files may expire and need renewal.

## 6. Create the pipeline configuration

Inside `frappe-doc-automation`, create `pilot.json` (local only):

```json
{
  "base_url": "https://your-staging-site.example.com",
  "max_pages": 20,
  "redact_selectors": [
    ".navbar .avatar"
  ],
  "roles": [
    {
      "name": "Manager",
      "storage_state": "~/.config/frappe-doc-pilot/manager-state.json"
    }
  ],
  "ai_model": "gpt-4.1-mini",
  "target_repo": "Aakvatech-Limited/av_rsvp",
  "documentation_branch": "docs/automated-frappe-guide"
}
```

**What these settings mean:**

| Setting | Purpose |
| --- | --- |
| `base_url` | HTTPS address of the sanitized staging site. |
| `max_pages` | Maximum number of inferred routes attempted (including `/app`). Start small. |
| `redact_selectors` | CSS selectors hidden *before* screenshots. Expand for your test site's sensitive UI. |
| `roles` | One separately authenticated browser session per documented role. |
| `ai_model` | OpenAI model used only with `--ai`. |
| `target_repo` | Destination repository used only with `--pr`. |
| `documentation_branch` | Branch name in the target repository for the documentation PR. |

> **Security limits:** CSS-selector hiding is not a comprehensive privacy filter. You must use sanitized demonstration data and inspect every PNG before publishing. The current screenshot engine tests the final page host but is not a network sandbox; keep outbound access restricted to trusted hosts. Capture failures on inferred routes can be skipped; missing screenshots need manual review.

## 7. Capture real screenshots and embed them into Markdown

```bash
frappe-docs pipeline \
  --repo ../av_rsvp \
  --output ./generated-docs \
  --config ./pilot.json
```

The pipeline will:

1. Rebuild the metadata reference pages.
2. Infer desktop, DocType list, and Query Report routes.
3. Open the staging site using the stored session for each configured role.
4. Save screenshots of successfully captured pages under `screenshots/<role>/`.
5. Link matching DocType list screenshots in the generated DocType Markdown pages.
6. Validate local Markdown links.

Check the output:

```text
generated-docs/
├── index.md
├── catalogue.json
├── routes.json
├── <app>-<doctype>.md
└── screenshots/
    └── manager/
        ├── desk.png
        └── <app>-<doctype>.png
```

Names vary with discovered DocTypes, permissions, and successful captures. **Not every captured page is automatically embedded:** the current renderer links matching DocType screenshots, while the desktop and report PNGs may remain separate.

Open one generated Markdown file and verify that its screenshot opens. If no screenshots were saved, check whether the account was authenticated, the route exists, and the user has permission to access it. Inspect the staging page manually if an inferred route is wrong.

To test only a known page, you may instead use the original `frappe-docs screenshots` command with a manually edited copy of `examples/screenshots.example.json`.

## 8. Optionally generate an AI-assisted user-guide draft

Set an API key securely, without writing it into `pilot.json`:

```bash
export OPENAI_API_KEY="YOUR_KEY_FROM_SECURE_SECRET_STORE"
```

Avoid saving this command with a real secret in shell history. Prefer a secret manager or ephemeral environment injection. Then run:

```bash
frappe-docs pipeline \
  --repo ../av_rsvp \
  --output ./generated-docs \
  --config ./pilot.json \
  --ai
```

Look for `generated-docs/ai-guide-draft.md`. This draft is based on repository metadata sent to the OpenAI API. It **does not** inspect live screenshots, understand every server/controller method, or verify actual permissions. A subject-matter reviewer must check every procedure against the live test site, remove unsupported claims, and decide what can be published.

If the environment variable is missing, the pipeline does **not** produce an AI guide; check the command's `ai_draft` result.

## 9. Preview the Frappe Docs-inspired site

The repository includes a MkDocs Material theme with search, navigation and light/dark mode. The theme is a **local static-site preview**, not a deployed Frappe Wiki.

From the tool repository:

```bash
mkdir -p site/docs/generated
cp -R generated-docs/. site/docs/generated/
python -m mkdocs serve -f site/mkdocs.yml
```

Open the local address printed by MkDocs (normally `http://127.0.0.1:8000`). Navigate to `Generated` and review the pages and screenshots. Verify links in both light and dark mode.

To produce static HTML for hosting:

```bash
python -m mkdocs build -f site/mkdocs.yml
```

The default HTML build directory is `site/site/` when invoked with this configuration unless you change `site_dir`. Build the site **only after** copying the new Markdown into `site/docs/generated/`; the pipeline does not currently perform this copy or deploy the website.

## 10. Optionally create a documentation PR in av_rsvp

First, inspect all generated Markdown and screenshots. Never publish screenshot files containing private or customer data.

Install GitHub CLI, authenticate, and verify access:

```bash
gh auth login
gh auth status
gh repo view Aakvatech-Limited/av_rsvp
git config user.name "Documentation Automation"
git config user.email "your-approved-git-email@example.com"
```

With `target_repo` configured in `pilot.json`, run the pipeline with `--pr`:

```bash
frappe-docs pipeline \
  --repo ../av_rsvp \
  --output ./generated-docs \
  --config ./pilot.json \
  --pr
```

This uses an authenticated `gh` CLI to clone the target, create the configured branch, copy generated files to `docs/generated/`, commit, push, and open a **draft PR**. The tool does not auto-merge. The current implementation expects the configured branch not to exist already in the cloned target and does not handle subsequent updates to the same branch gracefully. For a repeat pilot, use a new branch name or reconcile the existing branch manually.

Do **not** add `--ai` or `--pr` until you have reviewed the metadata and screenshots locally.

## 11. Completion checklist

- [ ] `pytest -q` passed.
- [ ] `--dry-run` printed plausible app routes.
- [ ] `generated-docs/index.md` and `catalogue.json` exist.
- [ ] Metadata pages reflect the correct DocTypes and fields.
- [ ] `frappe-docs validate` completed without broken links.
- [ ] Staging account was authenticated and a PNG was captured.
- [ ] At least one Markdown page opens its associated PNG.
- [ ] Screenshots have been checked for confidential information.
- [ ] Optional AI draft was reviewed against the live site.
- [ ] MkDocs preview displays navigable pages.
- [ ] Optional GitHub PR contains only intended files and remains draft until review.

## 12. Troubleshooting

| Symptom | What to check |
| --- | --- |
| `frappe-docs: command not found` | Activate `.venv` and reinstall with `pip install -e '.[test,browser,site]'`. |
| `No Frappe app discovered` | Confirm `--repo` and the package's `hooks.py` / `modules.txt`. |
| `Missing storage state` | Confirm the file exists and the configured path is correct. |
| Redirected to login | Recreate authenticated state; the session may have expired. |
| No screenshot for a page | Check permissions, inferred route, browser runtime, and staging-site connectivity. |
| Markdown has no screenshots | Matching DocType screenshot wasn't captured; report/desk screenshots are not automatically linked. |
| `ai_draft: false` | Set `OPENAI_API_KEY` and use `--ai`. |
| AI API error | Check credentials, API access, model availability and outbound connectivity. |
| MkDocs cannot find the content | Copy `generated-docs/` into `site/docs/generated/`. |
| GitHub PR fails | Check `gh auth status`, push permission, Git identity, and whether the target branch already exists. |

## 13. What to expect from this pilot

The first milestone is a **source-backed reference manual with selected real screen captures**. It is not yet a complete task-by-task ERPNext manual. Missing capabilities include automatic record-level Form browsing, detailed workflow behavior verification, deep role-permission auditing, and reliable screenshot privacy detection. Use pilot findings to prioritize those improvements rather than assuming every generated page is publication-ready.
