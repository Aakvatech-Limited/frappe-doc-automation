"""Optional AI narrative draft. Never treat model output as verified UI behavior."""
import json
import os
import urllib.request
from pathlib import Path


def write_draft(catalogue: dict, output: Path, model: str = "gpt-4.1-mini") -> bool:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return False
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": (
                "Write concise user-facing Markdown from supplied Frappe metadata. "
                "Only state facts visible in metadata. Do not invent actions, business rules, "
                "screens, role access or workflows. State 'Requires site verification' "
                "for missing information. This is an editorial draft.")},
            {"role": "user", "content": json.dumps(catalogue, ensure_ascii=False)[:90000]},
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        draft = json.load(response)["choices"][0]["message"]["content"]
    (output / "ai-guide-draft.md").write_text(
        "> **Draft: human verification required before publication.**\n\n" +
        draft + "\n", encoding="utf-8")
    return True
