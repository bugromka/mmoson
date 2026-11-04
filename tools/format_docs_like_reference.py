#!/usr/bin/env python3
"""Apply the simple A4/Aptos document style observed in the supplied PDF sample.

This is a formatting-only pass: paragraph text, table data, images, and their order
are preserved.  The script can be rerun on either or both combined Edition 8 DOCX
files; it does not need the reference PDF at runtime.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS = (
    ROOT / "sections/MMOSON_combined_document_ru.docx",
    ROOT / "sections/MMOSON_combined_document_en.docx",
)

FONT = "Aptos"
BLACK = RGBColor(0, 0, 0)
BODY_PT = 14
TABLE_PT = 11
TITLE_PT = 16
SPECIAL_FONT_NAMES = {"cambria math", "cambrimath", "symbol", "symbolmt"}

HEADING_STYLES = {"Heading 1", "Heading 2", "Heading 3", "Heading 4"}
LIST_STYLES = {"List Bullet", "List Number", "List Paragraph"}
COMPONENT_MARKER = re.compile(
    r"^(?:Редакция 8|Edition 8)\s*·.*\b(?:документ|document)\s+\d+",
    re.IGNORECASE,
)


def _set_rfonts(rpr, font_name: str) -> None:
    """Set all Word script slots, not only the Latin font name."""
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{attr}"), font_name)


def _set_style_font(style, size_pt: float, *, bold: bool | None = None) -> None:
    style.font.name = FONT
    style.font.size = Pt(size_pt)
    style.font.color.rgb = BLACK
    if bold is not None:
        style.font.bold = bold
    _set_rfonts(style._element.get_or_add_rPr(), FONT)


def _paragraph_runs(paragraph):
    """Include runs inside hyperlinks as well as ordinary paragraph runs."""
    for element in paragraph._p.xpath(".//w:r"):
        yield Run(element, paragraph)


def _iter_tables(document):
    """Yield top-level and nested tables once."""
    seen_tables: set[int] = set()

    def walk(table):
        key = id(table._tbl)
        if key in seen_tables:
            return
        seen_tables.add(key)
        yield table
        for row in table.rows:
            for cell in row.cells:
                # Merged cells can be encountered repeatedly; seen_tables prevents
                # their nested tables from being formatted more than once.
                for nested in cell.tables:
                    yield from walk(nested)

    for table in document.tables:
        yield from walk(table)


def _set_run_style(run: Run, size_pt: float, *, force_bold: bool | None = None) -> None:
    if not run.text:
        return
    current_name = (run.font.name or "").casefold()
    if current_name not in SPECIAL_FONT_NAMES:
        run.font.name = FONT
        _set_rfonts(run._r.get_or_add_rPr(), FONT)
    run.font.size = Pt(size_pt)
    run.font.color.rgb = BLACK
    if force_bold is not None:
        run.bold = force_bold


def _add_or_get_child(parent, tag: str, before: tuple[str, ...] = ()):
    element = parent.find(qn(tag))
    if element is not None:
        return element
    element = OxmlElement(tag)
    before_tags = {qn(name) for name in before}
    insert_at = next(
        (i for i, child in enumerate(parent) if child.tag in before_tags),
        len(parent),
    )
    parent.insert(insert_at, element)
    return element


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = _add_or_get_child(
        tbl_pr,
        "w:tblBorders",
        before=("w:tblLayout", "w:tblLook", "w:tblCellMar"),
    )
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        border = borders.find(tag)
        if border is None:
            border = OxmlElement(f"w:{edge}")
            borders.append(border)
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")  # 0.5 pt, as in the sample's black grid.
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "000000")


def _set_table_cell_margins(table) -> None:
    tbl_pr = table._tbl.tblPr
    margins = _add_or_get_child(tbl_pr, "w:tblCellMar", before=("w:tblLook",))
    for side, width in (("top", 0), ("bottom", 0), ("left", 80), ("right", 80)):
        tag = qn(f"w:{side}")
        margin = margins.find(tag)
        if margin is None:
            margin = OxmlElement(f"w:{side}")
            margins.append(margin)
        margin.set(qn("w:w"), str(width))
        margin.set(qn("w:type"), "dxa")


def _format_tables(document) -> None:
    for table in _iter_tables(document):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        try:
            table.style = document.styles["Table Grid"]
        except KeyError:
            pass
        _set_table_borders(table)
        _set_table_cell_margins(table)

        for row_index, row in enumerate(table.rows):
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tc_pr = cell._tc.get_or_add_tcPr()
                shading = tc_pr.find(qn("w:shd"))
                if shading is not None:
                    tc_pr.remove(shading)
                cell_borders = tc_pr.find(qn("w:tcBorders"))
                if cell_borders is not None:
                    tc_pr.remove(cell_borders)
                for paragraph in cell.paragraphs:
                    fmt = paragraph.paragraph_format
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    fmt.line_spacing = 1.0
                    fmt.space_before = Pt(0)
                    fmt.space_after = Pt(0)
                    fmt.left_indent = Pt(0)
                    fmt.right_indent = Pt(0)
                    fmt.first_line_indent = Pt(0)
                    is_header = row_index == 0 and bool(paragraph.text.strip())
                    for run in _paragraph_runs(paragraph):
                        _set_run_style(run, TABLE_PT, force_bold=True if is_header else None)


def _title_block_indices(paragraphs) -> set[int]:
    start = next(
        (
            i for i, paragraph in enumerate(paragraphs)
            if "о публикации" in paragraph.text.casefold()
            or "about the publication" in paragraph.text.casefold()
        ),
        None,
    )
    if start is None:
        return set()
    end = next(
        (
            i for i in range(start, len(paragraphs))
            if "курск" in paragraphs[i].text.casefold()
            or "kursk" in paragraphs[i].text.casefold()
        ),
        len(paragraphs) - 1,
    )
    return set(range(start, end + 1))


def _is_toc_note(text: str) -> bool:
    value = text.casefold()
    return "содержание обновляется автоматически" in value or "table of contents updates automatically" in value


def _is_component_marker(text: str) -> bool:
    return bool(COMPONENT_MARKER.match(text.strip()))


def _contains_drawing(paragraph) -> bool:
    return bool(paragraph._p.xpath(".//w:drawing"))


def _set_paragraph_format(paragraph, *, size_pt: float, bold: bool | None,
                          alignment, line_spacing: float,
                          before_pt: float, after_pt: float) -> None:
    fmt = paragraph.paragraph_format
    paragraph.alignment = alignment
    fmt.line_spacing = line_spacing
    fmt.space_before = Pt(before_pt)
    fmt.space_after = Pt(after_pt)
    fmt.first_line_indent = Pt(0)
    if paragraph.style.name not in LIST_STYLES:
        fmt.left_indent = Pt(0)
        fmt.right_indent = Pt(0)
    for run in _paragraph_runs(paragraph):
        _set_run_style(run, size_pt, force_bold=bold)


def _format_paragraphs(document) -> None:
    paragraphs = document.paragraphs
    title_indices = _title_block_indices(paragraphs)
    for paragraph_index, paragraph in enumerate(paragraphs):
        text = paragraph.text.strip()
        if not text:
            # Keep blank lines and existing image spacing; they carry intentional layout.
            continue
        if _contains_drawing(paragraph):
            # Preserve the existing centered image paragraphs and their spacing.
            continue

        style_name = paragraph.style.name

        if _is_component_marker(text):
            _set_paragraph_format(
                paragraph, size_pt=9, bold=None,
                alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.0,
                before_pt=0, after_pt=2,
            )
        elif _is_toc_note(text):
            _set_paragraph_format(
                paragraph, size_pt=11, bold=False,
                alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.1,
                before_pt=0, after_pt=4,
            )
        elif style_name in HEADING_STYLES:
            _set_paragraph_format(
                paragraph, size_pt=BODY_PT, bold=True,
                alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.4,
                before_pt=10, after_pt=8,
            )
            paragraph.paragraph_format.keep_with_next = True
        elif style_name == "Caption":
            _set_paragraph_format(
                paragraph, size_pt=TABLE_PT, bold=True,
                alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.0,
                before_pt=5, after_pt=5,
            )
        elif style_name == "Title":
            _set_paragraph_format(
                paragraph, size_pt=TITLE_PT, bold=True,
                alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.4,
                before_pt=0, after_pt=0,
            )
            paragraph.paragraph_format.keep_with_next = True
        elif paragraph_index in title_indices:
            lower = text.casefold()
            if "о публикации" in lower or "about the publication" in lower:
                size_pt, bold, alignment, after_pt = BODY_PT, True, WD_ALIGN_PARAGRAPH.LEFT, 8
            elif text.upper() in {"АВТОРЫ", "AUTHORS"}:
                size_pt, bold, alignment, after_pt = BODY_PT, True, WD_ALIGN_PARAGRAPH.CENTER, 5
            elif text.startswith("(") and ("ММОСО" in text.upper() or "MMOSO" in text.upper()):
                size_pt, bold, alignment, after_pt = TITLE_PT, True, WD_ALIGN_PARAGRAPH.CENTER, 0
            else:
                direct_sizes = [run.font.size.pt for run in paragraph.runs if run.text.strip() and run.font.size]
                size_pt = TITLE_PT if direct_sizes and max(direct_sizes) >= 18 else BODY_PT
                bold = True if size_pt == TITLE_PT else None
                alignment = paragraph.alignment if paragraph.alignment is not None else WD_ALIGN_PARAGRAPH.CENTER
                after_pt = 0 if size_pt == TITLE_PT else 5
            _set_paragraph_format(
                paragraph, size_pt=size_pt, bold=bold,
                alignment=alignment, line_spacing=1.4,
                before_pt=0, after_pt=after_pt,
            )
        else:
            # The sample uses a left-aligned 14 pt body. Keep centered cover lines,
            # equations, and other intentional alignment; replace full justification.
            alignment = paragraph.alignment
            if alignment in (None, WD_ALIGN_PARAGRAPH.JUSTIFY):
                alignment = WD_ALIGN_PARAGRAPH.LEFT
            _set_paragraph_format(
                paragraph, size_pt=BODY_PT, bold=None,
                alignment=alignment, line_spacing=1.4,
                before_pt=0, after_pt=8,
            )


def _format_cover(document) -> None:
    """Position the cover title, project lead and location like the PDF sample."""
    paragraphs = document.paragraphs
    if len(paragraphs) < 4:
        return

    title = paragraphs[0]
    edition = paragraphs[1]
    author = next(
        (p for p in paragraphs[:8] if p.text.startswith(("Руководитель:", "Project lead:"))),
        None,
    )
    city = next(
        (p for p in paragraphs[:8] if p.text.startswith(("Курск,", "Kursk,"))),
        None,
    )
    marker = next((p for p in paragraphs if _is_component_marker(p.text)), None)

    _set_paragraph_format(
        title, size_pt=TITLE_PT, bold=True,
        alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.4,
        before_pt=0, after_pt=0,
    )
    _set_paragraph_format(
        edition, size_pt=11, bold=False,
        alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.1,
        before_pt=2, after_pt=0,
    )
    if author is not None:
        _set_paragraph_format(
            author, size_pt=BODY_PT, bold=False,
            alignment=WD_ALIGN_PARAGRAPH.RIGHT, line_spacing=1.4,
            before_pt=340, after_pt=0,
        )
    if city is not None:
        _set_paragraph_format(
            city, size_pt=BODY_PT, bold=False,
            alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.4,
            before_pt=270, after_pt=0,
        )
    if marker is not None:
        marker.paragraph_format.page_break_before = True
        marker.paragraph_format.keep_with_next = True


def _format_styles(document) -> None:
    for style in document.styles:
        if style.type != WD_STYLE_TYPE.PARAGRAPH:
            continue
        name = style.name
        size = TABLE_PT if name == "Caption" else TITLE_PT if name == "Title" else BODY_PT
        force_bold = True if name in HEADING_STYLES or name in {"Title", "Caption"} else None
        _set_style_font(style, size, bold=force_bold)
        fmt = style.paragraph_format
        if name in HEADING_STYLES:
            fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
            fmt.line_spacing = 1.4
            fmt.space_before = Pt(10)
            fmt.space_after = Pt(8)
            fmt.keep_with_next = True
        elif name == "Caption":
            fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fmt.line_spacing = 1.0
            fmt.space_before = Pt(5)
            fmt.space_after = Pt(5)
        elif name == "Title":
            fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fmt.line_spacing = 1.4
            fmt.space_before = Pt(0)
            fmt.space_after = Pt(0)
            fmt.keep_with_next = True
        elif name in LIST_STYLES:
            fmt.line_spacing = 1.4
            fmt.space_after = Pt(8)
        elif name in {"Header", "Footer"}:
            fmt.line_spacing = 1.0


def format_document(path: Path) -> None:
    document = Document(path)
    for section in document.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.5)

    _format_styles(document)
    _format_tables(document)
    _format_paragraphs(document)
    _format_cover(document)

    temporary = path.with_name(path.stem + ".formatting.tmp.docx")
    document.save(temporary)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="*", type=Path,
        help="DOCX file(s) to format; defaults to both combined Edition 8 documents.",
    )
    args = parser.parse_args()
    paths = [path if path.is_absolute() else ROOT / path for path in args.files] if args.files else list(DEFAULT_DOCS)
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"DOCX file not found: {path}")
        format_document(path)
        print(f"Formatted: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
