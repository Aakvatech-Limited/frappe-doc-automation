from pathlib import Path
from .render import slug


def embed_screenshots(catalogue: dict, output: Path, captures: dict) -> None:
    for app in catalogue["apps"]:
        for doc in app["doctypes"]:
            if doc["istable"]:
                continue
            stem = slug(app["name"] + "-" + doc["name"])
            page = output / (stem + ".md")
            if not page.is_file():
                continue
            lines = []
            for role, names in captures.items():
                image = output / "screenshots" / slug(role) / (stem + ".png")
                if stem in names and image.is_file():
                    lines.append("### " + role + "\n\n![" + doc["name"] + " — " + role +
                                 "](screenshots/" + slug(role) + "/" + stem + ".png)")
            if lines:
                page.write_text(page.read_text(encoding="utf-8") +
                                "\n## Verified screenshots\n\n" +
                                "\n\n".join(lines) + "\n", encoding="utf-8")
