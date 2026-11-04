#!/usr/bin/env python3
"""Build Russian and English Edition 8 publication DOCX files.

The input directory must contain the 43 bilingual per-component DOCX files.
Tables and figures are kept; text, tables and figures are split at the language
markers instead of flattening the document into paragraphs. The finalizer then
restores the 24-sheet set and embeds the matching language versions from
site/assets.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement
from docxcompose.composer import Composer
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "sections"
EXPECTED_COMPONENTS = 43
EDITION_DATE_RU = "31 октября 2026 г."
EDITION_DATE_EN = "31 October 2026"


def sort_key(path: Path) -> tuple[int, int, str]:
    """Keep front matter first, numbered sections in order, appendices last."""
    name = path.name
    if name.startswith("00_"):
        return (0, 0, name)
    match = re.match(r"(\d+)_", name)
    if match:
        return (1, int(match.group(1)), name)
    return (2, 0, name)


def is_reference_heading(text: str) -> bool:
    upper = text.upper()
    return "СПИСОК ЛИТЕРАТУРЫ РАЗДЕЛА" in upper or "REFERENCES OF THIS SECTION" in upper


def is_assumptions_heading(text: str) -> bool:
    return bool(re.match(r"\s*(?:Кроме того|In addition|Additionally)\b", text, re.IGNORECASE))


def has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", text))


def set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    """Replace text while keeping the paragraph's first-run formatting."""
    runs = paragraph.runs
    if runs:
        for run in runs[1:]:
            run._element.getparent().remove(run._element)
        runs[0].text = text
    else:
        paragraph.add_run(text)


FIGURE_DIRS = {
    "ru": ROOT / "site" / "assets" / "fig_ru",
    "en": ROOT / "site" / "assets" / "fig_en",
}
FIGURE_COUNT = 24

FIGURE_TEXT = {
    "ru": {
        "old_map_prefix": "Карта ресурсных тел программы вынесена из настоящего документа",
        "new_map_prefix": "Краткая схема орбит ресурсных тел приведена",
        "map_text": (
            "Краткая схема орбит ресурсных тел приведена на рисунке 22. Она показывает "
            "орбиты пяти ресурсных тел, орбиты Земли, Марса и Юпитера и положение станции "
            "в точке L1; точками отмечены перигелии. Полная карта «Ресурсная база "
            "программы» вынесена из настоящего документа отдельным листом формата A3, "
            "альбомная ориентация (420 × 297 мм), в файлах resource_map.png и "
            "resource_map.pdf. На полной карте показаны главный пояс астероидов, троянцы "
            "и пять ресурсных орбит с точками перигелия и афелия; текущие положения тел "
            "не отображаются. Диаметры пяти тел приведены в правой легенде вместе с их "
            "ресурсной ролью и орбитальными параметрами. Компоновка рассчитана на печать "
            "одним читаемым листом A3: карта занимает левую часть, а легенда источников и "
            "материальный баланс — правую."
        ),
        "caption": "Рисунок 22 — орбиты ресурсных тел в плоскости эклиптики",
        "alt_title": "Ресурсные тела: орбиты в плоскости эклиптики",
        "alt_descr": "Орбиты пяти ресурсных тел, Земли, Марса и Юпитера; положение станции в точке L1.",
        "caption_pattern": re.compile(r"^Рисунок\s+(\d+)\s+—"),
        "reference_pattern": re.compile(
            r"(?i)(\b(?:рисунок|рисунка|рисунке|рисунку|рис\.)\s+)(22|23)\b"
        ),
    },
    "en": {
        "old_map_prefix": "The map of program resource bodies is taken out from this document",
        "new_map_prefix": "A concise diagram of resource-body orbits is provided",
        "map_text": (
            "A concise diagram of resource-body orbits is provided in Figure 22. It shows "
            "the orbits of five resource bodies, the orbits of Earth, Mars and Jupiter, and "
            "the station at L1; dots mark perihelia. The full “Program Resource Base” map "
            "remains a separate A3 landscape sheet (420 × 297 mm; files resource_map.png "
            "and resource_map.pdf). The full map shows the main asteroid belt, the Trojans, "
            "and five resource orbits with perihelion and aphelion points; current body "
            "positions are not displayed. The diameters of the five bodies are listed in "
            "the right-hand legend together with their resource roles and orbital "
            "parameters. The layout is designed for one readable A3 print: the map occupies "
            "the left side, and the source legend and material balance the right."
        ),
        "caption": "Figure 22 - resource-body orbits in the ecliptic plane",
        "alt_title": "Resource bodies: orbits in the ecliptic plane",
        "alt_descr": "Orbits of five resource bodies, Earth, Mars and Jupiter; station location at L1.",
        "caption_pattern": re.compile(r"^Figure\s+(\d+)\s+[-–—]", re.IGNORECASE),
        "reference_pattern": re.compile(r"(?i)(\b(?:figure|fig\.)\s+)(22|23)\b"),
    },
}


def _figure_hashes() -> tuple[dict[str, str], dict[str, dict[str, Path]]]:
    """Return byte-hash-to-stem mapping and language-specific artwork paths."""
    hash_to_stem: dict[str, str] = {}
    by_language: dict[str, dict[str, Path]] = {"ru": {}, "en": {}}
    for language, folder in FIGURE_DIRS.items():
        files = sorted(folder.glob("fig*.png"))
        if len(files) != FIGURE_COUNT:
            raise RuntimeError(
                f"Expected {FIGURE_COUNT} {language.upper()} figure assets in {folder}, found {len(files)}"
            )
        by_language[language] = {path.stem: path for path in files}
        for path in files:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            prior = hash_to_stem.setdefault(digest, path.stem)
            if prior != path.stem:
                raise RuntimeError(f"Figure assets share a hash but have different names: {prior}, {path.stem}")
    return hash_to_stem, by_language


def _insert_paragraph_after(anchor: Paragraph, style) -> Paragraph:
    element = OxmlElement("w:p")
    anchor._p.addnext(element)
    paragraph = Paragraph(element, anchor._parent)
    if style is not None:
        paragraph.style = style
    return paragraph


def finalize_figures(output: Path, language: str) -> None:
    """Embed all 24 language-specific plates in a combined Edition 8 DOCX."""
    if language not in FIGURE_TEXT:
        raise ValueError(f"Unsupported document language: {language}")
    doc = Document(output)
    hash_to_stem, assets = _figure_hashes()
    figure_info = FIGURE_TEXT[language]
    changed = False
    # The bilingual source components currently carry Russian artwork in both
    # language blocks. Normalize every retained image to the output language.
    for shape in doc.inline_shapes:
        relationship_id = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        image_part = doc.part.related_parts[relationship_id]
        digest = hashlib.sha256(image_part.blob).hexdigest()
        stem = hash_to_stem.get(digest)
        if stem is None:
            raise RuntimeError(f"Unrecognized figure in {output.name}: {digest[:12]}")
        expected = assets[language][stem].read_bytes()
        if image_part.blob != expected:
            image_part._blob = expected
            changed = True

    if len(doc.inline_shapes) not in (FIGURE_COUNT - 1, FIGURE_COUNT):
        raise RuntimeError(
            f"{output.name}: expected 23 or 24 existing figures, found {len(doc.inline_shapes)}"
        )

    paragraphs = list(iter_container_paragraphs(doc))
    anchor_candidates = [
        paragraph for paragraph in paragraphs
        if paragraph.text.startswith(figure_info["old_map_prefix"])
        or paragraph.text.startswith(figure_info["new_map_prefix"])
    ]
    if len(anchor_candidates) != 1:
        raise RuntimeError(f"{output.name}: expected one resource-orbit map paragraph, found {len(anchor_candidates)}")
    map_paragraph = anchor_candidates[0]
    if map_paragraph.text != figure_info["map_text"]:
        set_paragraph_text(map_paragraph, figure_info["map_text"])
        changed = True

    caption_numbers = [
        int(match.group(1))
        for paragraph in doc.paragraphs
        if (match := figure_info["caption_pattern"].match(paragraph.text.strip()))
    ]
    if len(doc.inline_shapes) == FIGURE_COUNT - 1:
        if caption_numbers != list(range(1, FIGURE_COUNT)):
            raise RuntimeError(f"{output.name}: unexpected pre-insertion caption sequence {caption_numbers}")
        # The newly inserted resource-orbit plate takes Figure 22. Shift all
        # existing references to the quarantine and panel figures by one.
        for paragraph in iter_container_paragraphs(doc):
            if paragraph._p is map_paragraph._p:
                continue
            updated = figure_info["reference_pattern"].sub(
                lambda match: match.group(1) + str(int(match.group(2)) + 1),
                paragraph.text,
            )
            if updated != paragraph.text:
                set_paragraph_text(paragraph, updated)
                changed = True

        picture_paragraph = _insert_paragraph_after(map_paragraph, doc.styles["Normal"])
        picture_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        picture_paragraph.paragraph_format.first_line_indent = Cm(0)
        picture_paragraph.paragraph_format.space_before = Pt(10)
        picture_paragraph.paragraph_format.space_after = Pt(2)
        picture_paragraph.paragraph_format.keep_with_next = True
        picture = picture_paragraph.add_run().add_picture(
            str(assets[language]["fig22_asteroids"]), width=Cm(15.5)
        )
        picture._inline.docPr.title = figure_info["alt_title"]
        picture._inline.docPr.descr = figure_info["alt_descr"]

        caption_paragraph = _insert_paragraph_after(picture_paragraph, doc.styles["Caption"])
        caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_paragraph.paragraph_format.first_line_indent = Cm(0)
        caption_paragraph.add_run(figure_info["caption"])
        changed = True
    else:
        if caption_numbers != list(range(1, FIGURE_COUNT + 1)):
            raise RuntimeError(f"{output.name}: unexpected final caption sequence {caption_numbers}")
        if sum(p.text == figure_info["caption"] for p in doc.paragraphs) != 1:
            raise RuntimeError(f"{output.name}: localized Figure 22 caption is missing or duplicated")

    if changed:
        doc.save(output)

    # Reopen the package to ensure the final serialized publication contains
    # one of each plate and a consecutive caption sequence.
    check = Document(output)
    final_stems = []
    for shape in check.inline_shapes:
        relationship_id = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        image_part = check.part.related_parts[relationship_id]
        digest = hashlib.sha256(image_part.blob).hexdigest()
        stem = hash_to_stem.get(digest)
        if stem is None or image_part.blob != assets[language][stem].read_bytes():
            raise RuntimeError(f"{output.name}: embedded image is not localized for {language}")
        final_stems.append(stem)
    if len(final_stems) != FIGURE_COUNT or set(final_stems) != set(assets[language]):
        raise RuntimeError(f"{output.name}: final figure set is incomplete or duplicated: {final_stems}")
    if sum(paragraph.text == figure_info["map_text"] for paragraph in check.paragraphs) != 1:
        raise RuntimeError(f"{output.name}: resource-orbit map note is missing or duplicated")
    final_captions = [
        int(match.group(1))
        for paragraph in check.paragraphs
        if (match := figure_info["caption_pattern"].match(paragraph.text.strip()))
    ]
    if final_captions != list(range(1, FIGURE_COUNT + 1)):
        raise RuntimeError(f"{output.name}: final caption sequence is {final_captions}")


def document_number(doc: Document) -> int | None:
    for paragraph in doc.paragraphs:
        match = re.search(r"(?:документ|document)\s+(\d+)\s+(?:из|of)\s+43", paragraph.text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def component_title(path: Path, language: str) -> str:
    """Read the first title from the component's own Russian or English block."""
    if path.stem == "00_ОГЛАВЛЕНИЕ":
        return "Содержание публикации" if language == "ru" else "Table of Contents"
    if path.stem == "ЛИЦЕНЗИЯ":
        return "Лицензия и авторские права" if language == "ru" else "Licence and Copyright"

    doc = Document(path)
    marker = "РУССКАЯ РЕДАКЦИЯ" if language == "ru" else "ENGLISH EDITION"
    found_marker = False
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if marker in text.upper():
            found_marker = True
            continue
        if found_marker and text:
            return text
    return path.stem


def update_historical_notes(paragraph: Paragraph, language: str) -> None:
    text = paragraph.text
    if language == "ru" and "Редакционная отметка:" in text:
        text = text.replace(
            "Редакционная отметка: в редакции 15 сентября 2026 года рисунки 1–23 пересобраны",
            "Редакционная отметка: рисунки 1–23 были пересобраны 15 сентября 2026 года",
        )
        set_paragraph_text(paragraph, text)
    elif language == "en" and "Editorial note:" in text:
        text = text.replace(
            "Editorial note: in the 15 September 2026 revision, Figures 1–23 were regenerated",
            "Editorial note: Figures 1–23 were regenerated",
        )
        text = text.replace(
            "from the current source scripts.",
            "from the current source scripts on 15 September 2026.",
        )
        set_paragraph_text(paragraph, text)


def filter_component(path: Path, language: str) -> Document:
    """Keep one language block plus its references and publication assumptions."""
    doc = Document(path)
    body = doc.element.body
    nodes = list(body.iterchildren())
    marker = "РУССКАЯ РЕДАКЦИЯ" if language == "ru" else "ENGLISH EDITION"
    in_language = False
    in_references = False
    in_assumptions = False
    seen_references: set[str] = set()
    kept = []

    for node in nodes:
        if node.tag == qn("w:sectPr"):
            continue

        if node.tag == qn("w:p"):
            paragraph = Paragraph(node, doc)
            text = paragraph.text.strip()
            upper = text.upper()

            if marker in upper:
                in_language = True
                continue

            if language == "ru" and "ENGLISH EDITION" in upper:
                in_language = False
                continue

            if is_reference_heading(text):
                in_language = False
                in_references = True
                in_assumptions = False
                heading = "СПИСОК ЛИТЕРАТУРЫ РАЗДЕЛА" if language == "ru" else "REFERENCES OF THIS SECTION"
                set_paragraph_text(paragraph, heading)
                kept.append(node)
                continue

            if in_references:
                if is_assumptions_heading(text):
                    in_assumptions = True
                if in_assumptions:
                    cyrillic = has_cyrillic(text)
                    if (language == "ru" and not cyrillic) or (language == "en" and cyrillic):
                        continue
                elif text:
                    # Source references occur twice, once under each language.
                    # Keep each distinct citation once in the language document.
                    if text in seen_references:
                        continue
                    seen_references.add(text)
                kept.append(node)
                continue

            if in_language:
                update_historical_notes(paragraph, language)
                kept.append(node)
            continue

        # Tables and drawings are direct body children. Keep them only while
        # inside the selected language section. The composer remaps image and
        # hyperlink relationships when it appends each filtered component.
        if in_language:
            kept.append(node)
        elif in_references:
            kept.append(node)

    for node in list(body.iterchildren()):
        if node.tag != qn("w:sectPr"):
            body.remove(node)
    for node in kept:
        body.append(node)
    return doc


def make_master(files: list[Path], language: str) -> Document:
    """Create a publication shell using the first source's page setup/styles."""
    master = Document(files[0])
    body = master.element.body
    for node in list(body.iterchildren()):
        if node.tag != qn("w:sectPr"):
            body.remove(node)

    if language == "ru":
        title_text = "ММОСО’Н — техническая документация, редакция 8"
        subtitle = f"{EDITION_DATE_RU} · 43 компонента · 34 технических раздела"
        subject = f"Редакция 8; {EDITION_DATE_RU}; 43 компонента; 34 раздела"
    else:
        title_text = "MMOSO'N — Technical Documentation, Edition 8"
        subtitle = f"{EDITION_DATE_EN} · 43 components · 34 technical sections"
        subject = f"Edition 8; {EDITION_DATE_EN}; 43 components; 34 sections"

    title = master.add_heading(title_text, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    line = master.add_paragraph(subtitle)
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in line.runs:
        run.bold = True
        run.font.size = Pt(12)

    properties = master.core_properties
    properties.title = title_text
    properties.subject = subject
    properties.keywords = "MMOSO'N, Edition 8, technical documentation"
    return master


def add_component_stamp(master: Document, language: str, number: int | None) -> None:
    if language == "ru":
        text = f"Редакция 8 · {EDITION_DATE_RU}"
        text += f" · документ {number} из 43" if number is not None else " · содержание публикации"
    else:
        text = f"Edition 8 · {EDITION_DATE_EN}"
        text += f" · document {number} of 43" if number is not None else " · publication contents"
    paragraph = master.add_paragraph(text)
    paragraph.paragraph_format.page_break_before = True
    paragraph.paragraph_format.keep_with_next = True
    for run in paragraph.runs:
        run.italic = True
        run.font.size = Pt(9)


def add_english_contents(master: Document, files: list[Path]) -> None:
    """Create an English contents list from the actual component headings."""
    master.add_heading("Table of Contents", level=1)
    master.add_paragraph(
        "This publication contains 43 components, including 34 numbered technical sections, "
        "appendices and publication front matter."
    )
    table = master.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "No."
    table.rows[0].cells[1].text = "Component"
    for index, path in enumerate(files, 1):
        cells = table.add_row().cells
        cells[0].text = str(index)
        cells[1].text = component_title(path, "en")


def iter_container_paragraphs(container):
    """Yield paragraphs from a document part, including nested table cells."""
    yield from container.paragraphs
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from iter_container_paragraphs(cell)


def apply_project_spelling(doc: Document) -> None:
    """Use the requested Latin spelling in all visible DOCX text and metadata."""
    for paragraph in iter_container_paragraphs(doc):
        if "MMOSON" not in paragraph.text:
            continue
        for run in paragraph.runs:
            run.text = run.text.replace("MMOSON", "MMOSO'N")
        if "MMOSON" in paragraph.text:
            set_paragraph_text(paragraph, paragraph.text.replace("MMOSON", "MMOSO'N"))

    for section in doc.sections:
        for part in (
            section.header, section.footer,
            section.first_page_header, section.first_page_footer,
            section.even_page_header, section.even_page_footer,
        ):
            for paragraph in iter_container_paragraphs(part):
                if "MMOSON" not in paragraph.text:
                    continue
                for run in paragraph.runs:
                    run.text = run.text.replace("MMOSON", "MMOSO'N")
                if "MMOSON" in paragraph.text:
                    set_paragraph_text(paragraph, paragraph.text.replace("MMOSON", "MMOSO'N"))

    properties = doc.core_properties
    for key in ("title", "subject", "author", "keywords", "comments", "category"):
        value = getattr(properties, key, None)
        if isinstance(value, str):
            setattr(properties, key, value.replace("MMOSON", "MMOSO'N"))


def build_one(files: list[Path], output: Path, language: str) -> None:
    master = make_master(files, language)
    composer = Composer(master)

    for path in files:
        if language == "en" and path.stem == "00_ОГЛАВЛЕНИЕ":
            add_component_stamp(master, language, None)
            add_english_contents(master, files)
            continue

        source = Document(path)
        number = document_number(source)
        if language == "ru" and path.stem == "00_ОГЛАВЛЕНИЕ":
            # The publication's contents page is deliberately bilingual.
            filtered = source
            for paragraph in filtered.paragraphs:
                if "Статус документа: концептуальный проект; редакция 15 сентября 2026 г.;" in paragraph.text:
                    set_paragraph_text(
                        paragraph,
                        paragraph.text.replace(
                            "редакция 15 сентября 2026 г.",
                            "редакция 8 от 31 октября 2026 г.",
                        ),
                    )
        else:
            filtered = filter_component(path, language)

        add_component_stamp(master, language, number)
        composer.append(filtered)

    output.parent.mkdir(parents=True, exist_ok=True)
    composer.save(str(output))
    result = Document(output)
    apply_project_spelling(result)
    result.save(str(output))
    finalize_figures(output, language)
    result = Document(output)
    print(
        f"{output}: {output.stat().st_size / 1024 / 1024:.2f} MB; "
        f"{len(result.paragraphs)} paragraphs, {len(result.tables)} tables, "
        f"{len(result.inline_shapes)} figures"
    )


def source_components(source: Path) -> list[Path]:
    if not source.is_dir():
        raise SystemExit(f"Source directory does not exist: {source}")
    files = sorted(source.glob("*.docx"), key=sort_key)
    if len(files) != EXPECTED_COMPONENTS:
        raise SystemExit(
            f"Expected {EXPECTED_COMPONENTS} per-component DOCX files, found {len(files)} in {source}. "
            "Do not use the already-combined publication files as component input."
        )
    return files


def main(default_language: str = "both") -> int:
    parser = argparse.ArgumentParser(description="Assemble language-specific Edition 8 publication DOCX files.")
    parser.add_argument("--src", required=True, type=Path, help="directory with the 43 bilingual source DOCX components")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help=f"output directory (default: {DEFAULT_OUT})")
    parser.add_argument("--language", choices=("ru", "en", "both"), default=default_language)
    args = parser.parse_args()

    files = source_components(args.src)
    languages = ("ru", "en") if args.language == "both" else (args.language,)
    for language in languages:
        suffix = "ru" if language == "ru" else "en"
        output = args.out_dir / f"MMOSON_combined_document_{suffix}.docx"
        build_one(files, output, language)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
