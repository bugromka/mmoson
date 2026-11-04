#!/usr/bin/env python3
"""Verify Edition 8 structure, localization and front matter in both DOCX files."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SECTIONS = set(range(1, 35))
EXPECTED_COMPONENT_STAMPS = 42  # the contents page is not a numbered component
EXPECTED_FIGURES = 24
EXPECTED_BIBLIOGRAPHY_ENTRIES = 18

COMPONENT_STAMP = re.compile(
    r"^(?:Редакция 8|Edition 8)\s*·.*?\b(?:документ|document)\s+\d+\s+(?:из|of)\s+43\b",
    re.IGNORECASE,
)
LOCAL_REFERENCE_HEADING = re.compile(
    r"^(?:СПИСОК ЛИТЕРАТУРЫ РАЗДЕЛА|REFERENCES OF THIS SECTION)$",
    re.IGNORECASE,
)

PUBLICATIONS = {
    "ru": {
        "path": ROOT / "sections" / "MMOSON_combined_document_ru.docx",
        "title_marker": "редакция 8",
        "project_name": "ММОСО’Н",
        "cover_author": "Руководитель: Бугаенко Роман Сергеевич",
        "cover_city": "Курск, 2026",
        "stamp": re.compile(r"^Редакция 8 · 31 октября 2026 г\. · документ \d+ из 43$"),
        "section_heading": re.compile(r"^(\d{1,2})\."),
        "caption": re.compile(r"^Рисунок\s+(\d+)\s+—"),
        "subtitle": "43 компонента",
        "bibliography_heading": "ПРИЛОЖЕНИЕ Д. СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ",
        "matrix_heading": "ПРИЛОЖЕНИЕ Е. МАТРИЦА СТАТУСОВ И ПРОВЕРКИ",
        "matrix_notes_heading": "ОСНОВАНИЯ И ОГРАНИЧЕНИЯ ОЦЕНОК",
        "stale_patterns": (
            r"Документ дополнен 23",
            r"Рисунки 1–23",
            r"15 сентября 2026",
        ),
    },
    "en": {
        "path": ROOT / "sections" / "MMOSON_combined_document_en.docx",
        "title_marker": "edition 8",
        "project_name": "MMOSO'N",
        "cover_author": "Project lead: Roman Sergeevich Bugaenko",
        "cover_city": "Kursk, 2026",
        "stamp": re.compile(r"^Edition 8 · 31 October 2026 · document \d+ of 43$"),
        "section_heading": re.compile(r"^(\d{1,2})\."),
        "caption": re.compile(r"^Figure\s+(\d+)\s+[-–—]"),
        "subtitle": "43 components",
        "bibliography_heading": "APPENDIX E. REFERENCES",
        "matrix_heading": "APPENDIX F. STATUS AND VERIFICATION MATRIX",
        "matrix_notes_heading": "STATUS AND VERIFICATION NOTES",
        "stale_patterns": (
            r"supplemented with 23",
            r"Figures 1–23",
            r"15 September 2026",
        ),
    },
}

ENGLISH_STOPWORDS = re.compile(
    r"\b(?:this|these|those|the|and|of|to|in|is|are|was|were|be|been|being|with|from|by|for|"
    r"all|its|as|on|at|after|before|not|can|may|will|should|would|could|there|which|who|"
    r"when|where|our|your|their|only|each|over|under|while|without|about|into|between|"
    r"during|through|against|also|use|used|using|requires|does|rely|external|sources|"
    r"obtained|computation|values|section|document|table|figure|edition|public|reading|"
    r"permitted|other|written|permission)\b",
    re.IGNORECASE,
)
RUSSIAN_WORD = re.compile(r"[А-Яа-яЁё]{3,}")


def _bibliography_bounds(paragraphs: list[str], heading: str) -> tuple[int | None, int | None]:
    matches = [i for i, text in enumerate(paragraphs) if text == heading]
    if len(matches) != 1:
        return None, None
    start = matches[0]
    end = next(
        (i for i in range(start + 1, len(paragraphs)) if COMPONENT_STAMP.match(paragraphs[i])),
        len(paragraphs),
    )
    return start, end


def _numbered_entries(paragraphs: list[str], start: int, end: int) -> list[int]:
    numbers = []
    for text in paragraphs[start + 1:end]:
        match = re.match(r"^(\d+)\.\s", text)
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def _status_matrix_bullets(paragraphs: list[str], heading: str) -> tuple[int, int]:
    matches = [i for i, text in enumerate(paragraphs) if text == heading]
    if len(matches) != 1:
        return len(matches), 0
    start = matches[0]
    end = next(
        (i for i in range(start + 1, len(paragraphs)) if COMPONENT_STAMP.match(paragraphs[i])),
        len(paragraphs),
    )
    return len(matches), sum(text.strip().startswith("·") for text in paragraphs[start + 1:end])


def verify(language: str, spec: dict) -> list[str]:
    path: Path = spec["path"]
    errors: list[str] = []
    if not path.is_file():
        return [f"{language}: missing {path.relative_to(ROOT)}"]

    doc = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs]
    table_texts = [
        cell.text.strip()
        for table in doc.tables
        for row in table.rows
        for cell in row.cells
    ]
    all_text = "\n".join(paragraphs + table_texts)
    title = doc.core_properties.title or ""
    metadata = " ".join((title, doc.core_properties.subject or "", doc.core_properties.keywords or ""))

    if spec["project_name"] not in " ".join(paragraphs[:5]):
        errors.append(f"{language}: requested project spelling is missing from the visible cover")
    if "mmoson" in (all_text + "\n" + metadata).casefold():
        errors.append(f"{language}: obsolete MMOSON spelling remains in the document text or metadata")
    if language == "ru" and "MMOSO'N" in metadata:
        errors.append("ru: English project wording remains in DOCX metadata outside the shared bibliography")
    if spec["cover_author"] not in paragraphs[:5]:
        errors.append(f"{language}: cover does not show the project lead on a separate line")
    if spec["cover_city"] not in paragraphs[:5]:
        errors.append(f"{language}: cover does not show the city and year")
    if not paragraphs or "\n" not in paragraphs[0]:
        errors.append(f"{language}: cover title and project abbreviation are not on separate lines")

    first_stamp = next((p for p in doc.paragraphs if COMPONENT_STAMP.match(p.text.strip())), None)
    if first_stamp is None or not first_stamp.paragraph_format.page_break_before:
        errors.append(f"{language}: the first numbered component does not begin after the cover page")

    if spec["title_marker"] not in title.casefold():
        errors.append(f"{language}: Edition 8 is missing from the DOCX title properties")
    if not any(spec["title_marker"] in text.casefold() for text in paragraphs[:5]):
        errors.append(f"{language}: no visible Edition 8 title on the cover")
    if spec["subtitle"] not in " ".join(paragraphs[:5]):
        errors.append(f"{language}: cover does not state the 43-component publication scope")

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
    else:
        for table_index, table in enumerate(doc.tables, start=1):
            if table.style.name != "Table Grid":
                errors.append(f"{language}: table {table_index} is not using the plain Table Grid style")
                break
            if table.alignment != WD_TABLE_ALIGNMENT.CENTER:
                errors.append(f"{language}: table {table_index} is not centered")
                break
            borders = table._tbl.tblPr.find(qn("w:tblBorders"))
            expected_edges = ("top", "left", "bottom", "right", "insideH", "insideV")
            if borders is None or any(borders.find(qn(f"w:{edge}")) is None for edge in expected_edges):
                errors.append(f"{language}: table {table_index} is missing the thin grid borders")
                break
            for row in table.rows:
                for cell in row.cells:
                    if cell._tc.get_or_add_tcPr().find(qn("w:shd")) is not None:
                        errors.append(f"{language}: table {table_index} contains a filled cell")
                        break
                    if any(
                        paragraph.text.strip() and paragraph.alignment != WD_ALIGN_PARAGRAPH.CENTER
                        for paragraph in cell.paragraphs
                    ):
                        errors.append(f"{language}: table {table_index} has non-centered cell text")
                        break
                if errors:
                    break
            if errors:
                break

    if language == "ru":
        relevance = [i for i, text in enumerate(paragraphs) if text == "1.1. Актуальность"]
        if len(relevance) != 1:
            errors.append(f"ru: expected one existing 1.1 Relevance section, found {len(relevance)}")
        elif not any("Космическая колонизация" in text for text in paragraphs[relevance[0] + 1:relevance[0] + 3]):
            errors.append("ru: the existing 1.1 Relevance text is missing")

    for stale_pattern in spec["stale_patterns"]:
        if re.search(stale_pattern, all_text, re.IGNORECASE):
            errors.append(f"{language}: stale 23-figure/September 2026 wording remains: {stale_pattern}")
            break

    local_reference_count = sum(bool(LOCAL_REFERENCE_HEADING.fullmatch(text)) for text in paragraphs)
    if local_reference_count:
        errors.append(f"{language}: {local_reference_count} section-level bibliography headings remain")

    bib_start, bib_end = _bibliography_bounds(paragraphs, spec["bibliography_heading"])
    if bib_start is None or bib_end is None:
        errors.append(f"{language}: the one shared bibliography heading is missing or duplicated")
        bibliography_numbers = []
    else:
        bibliography_numbers = _numbered_entries(paragraphs, bib_start, bib_end)
        expected_numbers = list(range(1, EXPECTED_BIBLIOGRAPHY_ENTRIES + 1))
        if bibliography_numbers != expected_numbers:
            errors.append(
                f"{language}: shared bibliography must contain entries 1–{EXPECTED_BIBLIOGRAPHY_ENTRIES}; "
                f"found {bibliography_numbers}"
            )

    matrix_heading_count, matrix_bullet_count = _status_matrix_bullets(paragraphs, spec["matrix_heading"])
    if matrix_heading_count != 1:
        errors.append(f"{language}: expected one status/verification matrix, found {matrix_heading_count}")
    if matrix_bullet_count != 12:
        errors.append(f"{language}: expected 12 preserved status/verification notes, found {matrix_bullet_count}")
    if spec["matrix_notes_heading"] not in paragraphs:
        errors.append(f"{language}: the status matrix notes are missing their localized heading")

    if language == "ru":
        bibliography_range = set(range(bib_start, bib_end)) if bib_start is not None and bib_end is not None else set()
        non_bibliography = "\n".join(
            [text for i, text in enumerate(paragraphs) if i not in bibliography_range] + table_texts
        )
        forbidden = (
            "Лицензия / License",
            "CONTENTS OF THE PUBLICATION",
            "LIST OF ILLUSTRATIONS",
            "ABOUT THE PUBLICATION",
            "Island Three",
            "Earth-facing",
            "This section does not rely on external sources",
            "REFERENCES OF THIS SECTION",
            "Документ / Document",
            "Файл / File",
            "Источников / Sources",
            "Рисунок / Figure",
        )
        for phrase in forbidden:
            if phrase.casefold() in non_bibliography.casefold():
                errors.append(f"ru: English/bilingual wording remains outside the shared bibliography: {phrase}")
        english_matches = [
            text[:160]
            for text in non_bibliography.splitlines()
            if len(ENGLISH_STOPWORDS.findall(text)) >= 2
        ]
        if english_matches:
            errors.append(f"ru: English prose remains outside the shared bibliography: {english_matches[:3]}")
    else:
        bibliography_range = set(range(bib_start, bib_end)) if bib_start is not None and bib_end is not None else set()
        cyrillic_prose = []
        for i, text in enumerate(paragraphs):
            if i in bibliography_range:
                continue
            if any(len(word) >= 3 for word in RUSSIAN_WORD.findall(text)):
                cyrillic_prose.append(text[:160])
        cyrillic_prose.extend(
            text[:160]
            for text in table_texts
            if any(len(word) >= 3 for word in RUSSIAN_WORD.findall(text))
        )
        if cyrillic_prose:
            errors.append(f"en: Russian prose remains outside the shared bibliography: {cyrillic_prose[:3]}")

    print(
        f"{language}: Edition 8; {len(sections)} sections; {len(doc.tables)} tables; "
        f"{len(doc.inline_shapes)} figures; {stamp_count} component stamps; "
        f"{len(bibliography_numbers)} shared references; {matrix_bullet_count} matrix notes"
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
    print("PASS: covers, localization, one shared bibliography, status notes and Edition 8 sections are verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
