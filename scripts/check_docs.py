"""Fail when a local Markdown link points to a missing file."""
from pathlib import Path
import re


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    documents = [root / "README.md", *sorted((root / "docs").glob("*.md"))]
    missing = []
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = target.split("#", 1)[0]
            if path and not (document.parent / path).resolve().exists():
                missing.append((document.relative_to(root), target))
    print(f"Markdown files checked: {len(documents)}; missing local targets: {len(missing)}")
    for document, target in missing:
        print(f"{document}: {target}")
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())
