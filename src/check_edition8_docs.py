#!/usr/bin/env python3
"""Verify Edition 8 labels and structural contents of both combined DOCX files."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SECTIONS = set(range(1, 35))
EXPECTED_COMPONENT_STAMPS = 42  # the contents page is not a numbered component
EXPECTED_FIGURES = 24

PUBLICATIONS = {
    "ru": {
        "path": ROOT / "sections" / "MMOSON_combined_document_ru.docx",
        "title_marker": "редакция 8",
        "project_name": "ММОСО’Н",
        "stamp": re.compile(r"^Редакция 8 · 31 октября 2026 г\. · документ \d+ из 43$"),
        "section_heading": re.compile(r"^(\d{1,2})\."),
        "caption": re.compile(r"^Рисунок\s+(\d+)\s+—"),
        "subtitle": "43 компонента",
        "stale_revision": "редакция 15 сентября 2026 г.",
    },
    "en": {
        "path": ROOT / "sections" / "MMOSON_combined_document_en.docx",
        "title_marker": "edition 8",
        "project_name": "MMOSO'N",
        "stamp": re.compile(r"^Edition 8 · 31 October 2026 · document \d+ of 43$"),
        "section_heading": re.compile(r"^(\d{1,2})\."),
        "caption": re.compile(r"^Figure\s+(\d+)\s+[-–—]"),
        "subtitle": "43 components",
        "stale_revision": "in the 15 September 2026 revision",
    },
}


def verify(language: str, spec: dict) -> list[str]:
    path: Path = spec["path"]
    errors: list[str] = []
    if not path.is_file():
        return [f"{language}: missing {path.relative_to(ROOT)}"]

    doc = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs]
    table_text = "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )
    all_text = "\n".join(paragraphs) + "\n" + table_text
    title = doc.core_properties.title or ""
    metadata = " ".join((title, doc.core_properties.subject or "", doc.core_properties.keywords or ""))

    if spec["project_name"] not in " ".join(paragraphs[:5]):
        errors.append(f"{language}: requested project spelling is missing from the visible title")
    if "mmoson" in (all_text + "\n" + metadata).casefold():
        errors.append(f"{language}: obsolete MMOSON spelling remains in the document text or metadata")

    if spec["title_marker"] not in title.casefold():
        errors.append(f"{language}: Edition 8 is missing from the DOCX title properties")
    if not any(spec["title_marker"] in text.casefold() for text in paragraphs[:5]):
        errors.append(f"{language}: no visible Edition 8 title on the first page")
    if spec["subtitle"] not in " ".join(paragraphs[:5]):
        errors.append(f"{language}: first page does not state the 43-component publication scope")

    stamp_count = sum(bool(spec["stamp"].fullmatch(text)) for text in paragraphs)
    if stamp_count != EXPECTED_COMPONENT_STAMPS:
        errors.append(
            f"{language}: expected {EXPECTED_COMPONENT_STAMPS} dated component stamps, found {stamp_count}"
        )

    sections = {
        int(match.group(1))
        for text in paragraphs
        if (match := spec["section_heading"].match(text))
    }
    if sections != EXPECTED_SECTIONS:
        missing = sorted(EXPECTED_SECTIONS - sections)
        extra = sorted(sections - EXPECTED_SECTIONS)
        errors.append(f"{language}: numbered section set mismatch; missing={missing}, extra={extra}")

    captions = [
        int(match.group(1))
        for text in paragraphs
        if (match := spec["caption"].match(text))
    ]
    if captions != list(range(1, EXPECTED_FIGURES + 1)):
        errors.append(f"{language}: expected figure captions 1–{EXPECTED_FIGURES}, found {captions}")
    if len(doc.inline_shapes) != EXPECTED_FIGURES:
        errors.append(f"{language}: expected {EXPECTED_FIGURES} embedded figures, found {len(doc.inline_shapes)}")
    if not doc.tables:
        errors.append(f"{language}: no Word tables found")
    if spec["stale_revision"].casefold() in all_text.casefold():
        errors.append(f"{language}: stale September 2026 current-revision wording remains")

    print(
        f"{language}: Edition 8; {len(sections)} sections; {len(doc.tables)} tables; "
        f"{len(doc.inline_shapes)} figures; {stamp_count} component stamps"
    )
    return errors


def main() -> int:
    errors = []
    for language, spec in PUBLICATIONS.items():
        errors.extend(verify(language, spec))
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: both technical documents are explicitly Edition 8 and contain sections 1–34.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
