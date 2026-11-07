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
EXPECTED_TABLES = {"ru": 74, "en": 74}
EXPECTED_FIGURES = 24
EXPECTED_BIBLIOGRAPHY_ENTRIES = 61
EXPECTED_ABBREVIATIONS = 29
SOURCE_INVENTORY_HEADERS = {
    ("документ", "файл", "количество источников"),
    ("документ", "файл", "источников / sources"),
    ("документ / document", "файл / file", "источников / sources"),
    ("document", "file", "number of sources"),
    ("no.", "document", "file", "number of sources"),
    ("№", "документ", "файл", "количество источников"),
    ("№", "документ / document", "файл / file", "источников / sources"),
}
FIGURE_REGISTRY_HEADERS = {
    ("№", "рисунок", "подпись"),
    ("№", "рисунок", "раздел"),
    ("no.", "figure", "caption"),
    ("no.", "figure", "section"),
    ("№", "рисунок / figure", "подпись / caption"),
    ("no.", "figure", "caption / section"),
}
OPERATIONAL_SECTION_HEADINGS = {
    "ru": "11.17. Уроки эксплуатации МКС, «Салют», «Мир» и транспортных систем",
    "en": "11.17. Lessons from ISS, Salyut, Mir and crew-transport systems",
}
WATER_SCOPE_TERMS = {
    "ru": ("американского сегмента МКС", "сценарное допущение", "не доказательство работоспособности"),
    "en": ("U.S. segment", "scenario assumption", "not proof that the full water loop can operate"),
}
A4_LAYOUT_CM = {
    "page_width": 21.0,
    "page_height": 29.7,
    "top_margin": 2.0,
    "bottom_margin": 2.0,
    "left_margin": 3.0,
    "right_margin": 1.5,
}
BODY_FONT = "Times New Roman"
BODY_FONT_PT = 14
TABLE_FONT_PT = 12

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
        "stamp": re.compile(r"^Редакция 8 · 6 ноября 2026 г\. · документ \d+ из 43$"),
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
        "stamp": re.compile(r"^Edition 8 · 6 November 2026 · document \d+ of 43$"),
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
FOOD_REQUIREMENTS = {
    "ru": (
        "0,921625 трлн ккал/год",
        "1,3824375 трлн ккал",
        "33 215 т",
        "Потребители и направления продукции",
        "производственный план не рассчитан",
        "100 000 человек в год",
        "10 951 место единовременно",
    ),
    "en": (
        "0.921625 trillion kcal/year",
        "1.3824375 trillion kcal",
        "33,215 t",
        "Consumers and product destinations",
        "no production plan calculated",
        "100,000 people per year",
        "10,951 places at a time",
    ),
}
SCENARIO_SCOPE_TERMS = {
    "ru": ("прежнего сценария для одного цилиндра", "производственный план", "пищевых и кормовых потоков"),
    "en": ("former one-cylinder scenario", "production plan", "food and feed flows"),
}
CULTIVAR_TERMS = {
    "ru": ("Кандидатные сорта культур", "IR64", "ФОРМУЛА 1", "НЕВСКИЙ", "СИ ФЕНОМЕН", "6,6 растения/м²"),
    "en": ("Candidate crop cultivars", "IR64", "FORMULA 1", "NEVSKY", "SI FENOMEN", "6.6 plants/m²"),
}
EDIBLE_FISH_TERMS = {
    "ru": ("Белый амур (Ctenopharyngodon idella)", "Роху (Labeo rohita)", "Серебристый барбус (Barbonymus gonionotus)", "не называть строго травоядным"),
    "en": ("Grass carp (Ctenopharyngodon idella)", "Rohu (Labeo rohita)", "Silver barb (Barbonymus gonionotus)", "Not strictly herbivorous"),
}
WASTE_FLOW_TERMS = {
    "ru": ("сценарный субстрат", "не готовый корм", "не измеренный состав отходов", "не утверждённый контур переработки"),
    "en": ("scenario substrate", "not formulated feed", "not a measured waste composition", "not an approved processing circuit"),
}


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


def _check_reference_layout(doc, language: str) -> list[str]:
    errors: list[str] = []
    for section_index, section in enumerate(doc.sections, start=1):
        for attribute, expected_cm in A4_LAYOUT_CM.items():
            actual_cm = getattr(section, attribute).cm
            if abs(actual_cm - expected_cm) > 0.02:
                errors.append(
                    f"{language}: section {section_index} {attribute} is {actual_cm:.2f} cm; "
                    f"expected {expected_cm:.1f} cm"
                )
                break

    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    if normal_font.name != BODY_FONT:
        errors.append(f"{language}: Normal style font is {normal_font.name!r}; expected {BODY_FONT}")
    if normal_font.size is None or abs(normal_font.size.pt - BODY_FONT_PT) > 0.01:
        actual_pt = normal_font.size.pt if normal_font.size else None
        errors.append(f"{language}: Normal style size is {actual_pt}; expected {BODY_FONT_PT} pt")
    if normal_style.paragraph_format.line_spacing != 1.5:
        errors.append(f"{language}: Normal style line spacing is not 1.5")
    indent = normal_style.paragraph_format.first_line_indent
    if indent is None or abs(indent.cm - 1.25) > 0.02:
        actual_cm = indent.cm if indent is not None else None
        errors.append(f"{language}: Normal paragraph indent is {actual_cm} cm; expected 1.25 cm")

    for table_index, table in enumerate(doc.tables, start=1):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if not run.text.strip():
                            continue
                        if run.font.name != BODY_FONT or run.font.size is None or abs(run.font.size.pt - TABLE_FONT_PT) > 0.01:
                            actual_size = run.font.size.pt if run.font.size else None
                            errors.append(
                                f"{language}: table {table_index} cell text must use {BODY_FONT} {TABLE_FONT_PT} pt; "
                                f"found {run.font.name!r} {actual_size} pt"
                            )
                            return errors

    for section_index, section in enumerate(doc.sections, start=1):
        if not section.different_first_page_header_footer:
            errors.append(f"{language}: section {section_index} does not suppress the cover-page number")
        page_fields = " ".join(section.footer._element.xpath(".//w:instrText/text()"))
        if "PAGE" not in page_fields.upper():
            errors.append(f"{language}: section {section_index} is missing a page-number field")
        first_page_fields = section.first_page_footer._element.xpath(".//w:instrText/text()")
        if any("PAGE" in field.upper() for field in first_page_fields):
            errors.append(f"{language}: section {section_index} prints a page number on its cover")

    paragraphs = doc.paragraphs
    break_positions = []
    for index, paragraph in enumerate(paragraphs):
        if paragraph.paragraph_format.page_break_before:
            break_positions.append(index)
        if paragraph._p.xpath('.//w:br[@w:type="page"]'):
            break_positions.append(index)
    for earlier, later in zip(break_positions, break_positions[1:]):
        if not any(p.text.strip() for p in paragraphs[earlier + 1:later]):
            errors.append(f"{language}: consecutive page breaks with no content could create a blank page")
            break
    for paragraph in paragraphs:
        if COMPONENT_STAMP.match(paragraph.text.strip()) and not paragraph.paragraph_format.page_break_before:
            errors.append(f"{language}: a component stamp does not start on a new page")
            break
        if paragraph.style.name == "Heading 1" and paragraph.paragraph_format.page_break_before:
            errors.append(f"{language}: a Heading 1 duplicates the component-stamp page break")
            break
    return errors


def verify(language: str, spec: dict) -> list[str]:
    path: Path = spec["path"]
    errors: list[str] = []
    if not path.is_file():
        return [f"{language}: missing {path.relative_to(ROOT)}"]

    doc = Document(path)
    errors.extend(_check_reference_layout(doc, language))
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs]
    table_texts = [
        cell.text.strip()
        for table in doc.tables
        for row in table.rows
        for cell in row.cells
    ]
    obsolete_registries = []
    for table_index, table in enumerate(doc.tables, start=1):
        if not table.rows:
            continue
        headers = tuple(" ".join(cell.text.split()).casefold() for cell in table.rows[0].cells)
        if headers in SOURCE_INVENTORY_HEADERS:
            obsolete_registries.append(table_index)
    if obsolete_registries:
        errors.append(
            f"{language}: obsolete document/file/source-count registry table remains "
            f"(table indices {obsolete_registries})"
        )
    obsolete_figure_registries = []
    for table_index, table in enumerate(doc.tables, start=1):
        if not table.rows:
            continue
        headers = tuple(" ".join(cell.text.split()).casefold() for cell in table.rows[0].cells)
        if headers in FIGURE_REGISTRY_HEADERS:
            obsolete_figure_registries.append(table_index)
    if obsolete_figure_registries:
        errors.append(
            f"{language}: figure-register table remains instead of standalone captions "
            f"(table indices {obsolete_figure_registries})"
        )
    all_text = "\n".join(paragraphs + table_texts)
    for required_term in FOOD_REQUIREMENTS[language]:
        if required_term.casefold() not in all_text.casefold():
            errors.append(f"{language}: missing current food-flow requirement or status: {required_term}")
    for required_term in SCENARIO_SCOPE_TERMS[language]:
        if required_term.casefold() not in all_text.casefold():
            errors.append(f"{language}: missing archived-scenario qualification: {required_term}")
    for required_term in CULTIVAR_TERMS[language] + EDIBLE_FISH_TERMS[language]:
        if required_term.casefold() not in all_text.casefold():
            errors.append(f"{language}: missing cultivar, density or edible-fish reference: {required_term}")
    for required_term in WASTE_FLOW_TERMS[language]:
        if required_term.casefold() not in all_text.casefold():
            errors.append(f"{language}: waste-flow status/caveat is missing: {required_term}")
    if re.search(r"(?i)(?:virtual cities|minecraft|виртуальн\w*\s+город)", all_text):
        errors.append(f"{language}: obsolete virtual-city content remains")
    title = doc.core_properties.title or ""
    metadata = " ".join((title, doc.core_properties.subject or "", doc.core_properties.keywords or ""))

    if spec["project_name"] not in " ".join(paragraphs[:5]):
        errors.append(f"{language}: requested project spelling is missing from the visible cover")
    legacy_name_check = re.sub(
        r"(?i)(?:https?://)?(?:www\.)?mmoson\.space\b", "", all_text + "\n" + metadata
    )
    if re.search(r"(?i)\bmmoson\b", legacy_name_check):
        errors.append(f"{language}: obsolete MMOSON spelling remains outside the proposed domain reference")
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
        for paragraph in doc.paragraphs
        if paragraph.style.name in {"Heading 1", "Heading 2"}
        if (match := spec["section_heading"].match(paragraph.text.strip()))
    }
    if sections != EXPECTED_SECTIONS:
        missing = sorted(EXPECTED_SECTIONS - sections)
        extra = sorted(sections - EXPECTED_SECTIONS)
        errors.append(f"{language}: numbered section set mismatch; missing={missing}, extra={extra}")

    if paragraphs.count(OPERATIONAL_SECTION_HEADINGS[language]) != 1:
        errors.append(f"{language}: the source-based Section 11.17 is missing or duplicated")
    water_heading = "11.8. Замкнутый оборот воды" if language == "ru" else "11.8. Closed water circulation"
    next_water_heading = "11.9. Стоимость и правовой статус" if language == "ru" else "11.9. Cost and legal status"
    water_start = next((i for i, text in enumerate(paragraphs) if text == water_heading), None)
    water_end = next((i for i, text in enumerate(paragraphs) if text == next_water_heading), None)
    if water_start is None or water_end is None:
        errors.append(f"{language}: Section 11.8 water-scope qualification is missing")
    else:
        water_text = "\n".join(paragraphs[water_start:water_end])
        missing_water_terms = [term for term in WATER_SCOPE_TERMS[language] if term.casefold() not in water_text.casefold()]
        if missing_water_terms:
            errors.append(f"{language}: Section 11.8 lost its water-recovery scope caveats: {missing_water_terms}")

    captions = [
        int(match.group(1))
        for text in paragraphs
        if (match := spec["caption"].match(text))
    ]
    if captions != list(range(1, EXPECTED_FIGURES + 1)):
        errors.append(f"{language}: expected figure captions 1–{EXPECTED_FIGURES}, found {captions}")
    figure24 = next((
        text for text in paragraphs
        if (match := spec["caption"].match(text)) and int(match.group(1)) == 24
    ), "")
    figure24_caveat = "не рабочий проект" if language == "ru" else "not a working design"
    if figure24_caveat.casefold() not in figure24.casefold():
        errors.append(f"{language}: Figure 24 caption lacks its illustrative/non-design caveat")
    if len(doc.inline_shapes) != EXPECTED_FIGURES:
        errors.append(f"{language}: expected {EXPECTED_FIGURES} embedded figures, found {len(doc.inline_shapes)}")
    if len(doc.tables) != EXPECTED_TABLES[language]:
        errors.append(
            f"{language}: expected {EXPECTED_TABLES[language]} Edition 8 tables, found {len(doc.tables)}"
        )
    abbreviation_header = "Сокращение" if language == "ru" else "Abbreviation"
    abbreviation_tables = [
        table for table in doc.tables
        if table.rows and table.rows[0].cells
        and " ".join(table.rows[0].cells[0].text.split()) == abbreviation_header
    ]
    if len(abbreviation_tables) != 1:
        errors.append(f"{language}: expected one localized abbreviations table, found {len(abbreviation_tables)}")
    else:
        abbreviations = [" ".join(row.cells[0].text.split()) for row in abbreviation_tables[0].rows[1:]]
        if len(abbreviations) != EXPECTED_ABBREVIATIONS:
            errors.append(f"{language}: expected {EXPECTED_ABBREVIATIONS} abbreviations, found {len(abbreviations)}")
        if abbreviations != sorted(abbreviations, key=str.casefold):
            errors.append(f"{language}: abbreviation table is not alphabetically sorted")
        required_abbreviations = ("ИМТ", "Isp", "L1", "ppm") if language == "ru" else ("BMI", "HSDCI", "LSS", "RCIC")
        for abbreviation in required_abbreviations:
            if abbreviation not in abbreviations:
                errors.append(f"{language}: abbreviation table is missing {abbreviation}")
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
    if matrix_bullet_count != 15:
        errors.append(f"{language}: expected 15 status/verification notes (12 preserved plus 3 new scope notes), found {matrix_bullet_count}")
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
    print("PASS: covers, reference layout, localization, Edition 8 table counts, bibliography, status notes and sections are verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
