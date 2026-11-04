#!/usr/bin/env python3
"""Normalize the combined Edition 8 DOCX front matter and bibliography.

The source components are not present in this repository, so this script works
on the two already-combined final documents. It is safe to rerun: cover lines
are updated in place, repeated section-level reference blocks are removed, and
the one common bibliography plus the status matrix are retained.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK

ROOT = Path(__file__).resolve().parents[1]
DOCS = {
    "ru": ROOT / "sections" / "MMOSON_combined_document_ru.docx",
    "en": ROOT / "sections" / "MMOSON_combined_document_en.docx",
}
STAMP_RE = re.compile(
    r"^(?:Редакция 8|Edition 8)\s*·.*?\b(?:документ|document)\s+(\d+)\s+(?:из|of)\s+43\b",
    re.IGNORECASE,
)
LOCAL_REFERENCE_RE = re.compile(
    r"^(?:СПИСОК ЛИТЕРАТУРЫ РАЗДЕЛА|REFERENCES OF THIS SECTION)$",
    re.IGNORECASE,
)

COVER = {
    "ru": {
        "title": "Модуль моделирования орбитальной станции О’Нилла",
        "short_name": "ММОСО’Н",
        "edition": "Редакция 8 · 31 октября 2026 г. · 43 компонента · 34 технических раздела",
        "author": "Руководитель: Бугаенко Роман Сергеевич",
        "city": "Курск, 2026",
        "properties_title": "Модуль моделирования орбитальной станции О’Нилла — редакция 8",
        "properties_subject": "Техническая документация, редакция 8",
    },
    "en": {
        "title": "O’Neill Orbital Station Modeling Module",
        "short_name": "MMOSO'N",
        "edition": "Edition 8 · 31 October 2026 · 43 components · 34 technical sections",
        "author": "Project lead: Roman Sergeevich Bugaenko",
        "city": "Kursk, 2026",
        "properties_title": "O’Neill Orbital Station Modeling Module — Edition 8",
        "properties_subject": "Technical documentation, Edition 8",
    },
}


def _set_text(paragraph, text: str) -> None:
    paragraph.text = text


def _set_cover_title(paragraph, title: str, short_name: str) -> None:
    paragraph.clear()
    paragraph.add_run(title)
    paragraph.add_run().add_break(WD_BREAK.LINE)
    paragraph.add_run(f"({short_name})")


def _first_component_marker(document):
    for paragraph in document.paragraphs:
        match = STAMP_RE.match(paragraph.text.strip())
        if match and int(match.group(1)) == 1:
            return paragraph
    raise ValueError("component 1 edition stamp was not found")


def _cover_paragraph_before(marker, prefix: str):
    current = marker
    while current is not None:
        if current.text.startswith(prefix):
            return current
        parent = current._p.getparent()
        if parent is None:
            break
        siblings = list(parent)
        position = siblings.index(current._p)
        previous = next(
            (element for element in reversed(siblings[:position]) if element.tag.endswith("}p")),
            None,
        )
        if previous is None:
            break
        from docx.text.paragraph import Paragraph
        current = Paragraph(previous, marker._parent)
    return None


def _ensure_cover(document, language: str) -> None:
    spec = COVER[language]
    if not document.paragraphs:
        raise ValueError("document has no paragraphs")

    title = document.paragraphs[0]
    title.style = document.styles["Title"]
    _set_cover_title(title, spec["title"], spec["short_name"])

    if len(document.paragraphs) < 2:
        raise ValueError("document is missing its Edition 8 cover line")
    _set_text(document.paragraphs[1], spec["edition"])

    marker = _first_component_marker(document)
    author_prefix = "Руководитель:" if language == "ru" else "Project lead:"
    author = _cover_paragraph_before(marker, author_prefix)
    city_prefix = "Курск," if language == "ru" else "Kursk,"
    city = _cover_paragraph_before(marker, city_prefix)

    if author is None and city is None:
        author = marker.insert_paragraph_before(style="Normal")
        city = marker.insert_paragraph_before(style="Normal")
    elif author is None:
        author = city.insert_paragraph_before(style="Normal")
    elif city is None:
        city = marker.insert_paragraph_before(style="Normal")

    _set_text(author, spec["author"])
    _set_text(city, spec["city"])
    marker.paragraph_format.page_break_before = True
    marker.paragraph_format.keep_with_next = True

    properties = document.core_properties
    properties.title = spec["properties_title"]
    properties.subject = spec["properties_subject"]
    properties.author = "Бугаенко Роман Сергеевич" if language == "ru" else "Roman Sergeevich Bugaenko"
    properties.keywords = (
        "ММОСО’Н; редакция 8; орбитальная станция О’Нилла"
        if language == "ru"
        else "MMOSO'N; Edition 8; O'Neill orbital station"
    )


def _component_number(text: str) -> int | None:
    match = STAMP_RE.match(text.strip())
    return int(match.group(1)) if match else None


def _remove_repeated_reference_blocks(document, language: str) -> int:
    """Remove section reference blocks; keep the shared list and matrix notes."""
    matrix_heading = (
        "ОСНОВАНИЯ И ОГРАНИЧЕНИЯ ОЦЕНОК"
        if language == "ru"
        else "STATUS AND VERIFICATION NOTES"
    )
    removed = 0
    component: int | None = None
    index = 0

    while index < len(document.paragraphs):
        paragraph = document.paragraphs[index]
        marker_component = _component_number(paragraph.text)
        if marker_component is not None:
            component = marker_component

        if not LOCAL_REFERENCE_RE.fullmatch(paragraph.text.strip()):
            index += 1
            continue

        if component == 41:
            _set_text(paragraph, matrix_heading)
            paragraph.style = document.styles["Heading 2"]
            index += 1
            continue

        paragraphs = document.paragraphs
        end = index + 1
        while end < len(paragraphs) and _component_number(paragraphs[end].text) is None:
            end += 1
        for item in paragraphs[index:end]:
            parent = item._p.getparent()
            if parent is not None:
                parent.remove(item._p)
                removed += 1
        # The next item at this index is the following component stamp (if any).
        # Revisit it so the component number is updated before checking more text.

    return removed


def _translate_ru_labels_and_phrases(document) -> int:
    changed = 0
    exact_replacements = {
        "ПЕРЕЧЕНЬ ИЛЛЮСТРАЦИЙ / LIST OF ILLUSTRATIONS": "ПЕРЕЧЕНЬ ИЛЛЮСТРАЦИЙ",
        "О ПУБЛИКАЦИИ / ABOUT THE PUBLICATION": "О ПУБЛИКАЦИИ",
        "Двухцилиндровая конфигурация Island Three": "Двухцилиндровая конфигурация «Остров-3»",
    }
    removals = {"CONTENTS OF THE PUBLICATION"}

    for paragraph in list(document.paragraphs):
        text = paragraph.text.strip()
        if text in removals:
            parent = paragraph._p.getparent()
            if parent is not None:
                parent.remove(paragraph._p)
                changed += 1
            continue
        replacement = exact_replacements.get(text)
        if replacement is not None:
            _set_text(paragraph, replacement)
            changed += 1

        for run in paragraph.runs:
            original = run.text
            updated = original
            updated = updated.replace("Island Three", "«Остров-3»")
            updated = updated.replace("номинально связной и Earth-facing", "номинально ориентированный в сторону Земли")
            updated = updated.replace("номинально Earth-facing", "номинально ориентированный в сторону Земли")
            updated = updated.replace("Earth-facing", "ориентированный в сторону Земли")
            updated = updated.replace("О'Нилла", "О’Нилла")
            updated = updated.replace("о'нилла", "о’нилла")
            updated = updated.replace("О'Нилл", "О’Нилл")
            updated = updated.replace("о'нилл", "о’нилл")
            updated = updated.replace("ММОСО'Н", "ММОСО’Н")
            if updated != original:
                run.text = updated
                changed += 1

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        original = run.text
                        updated = original.replace("ММОСО'Н", "ММОСО’Н")
                        updated = updated.replace("О'Нилла", "О’Нилла")
                        if updated != original:
                            run.text = updated
                            changed += 1
                    table_labels = {
                        "Документ / Document": "Документ",
                        "Файл / File": "Файл",
                        "Источников / Sources": "Количество источников",
                        "Рисунок / Figure": "Рисунок",
                    }
                    value = paragraph.text.strip()
                    if value in table_labels:
                        _set_text(paragraph, table_labels[value])
                        changed += 1

    return changed


def _update_english_front_matter(document) -> int:
    changed = 0
    component: int | None = None
    for paragraph in document.paragraphs:
        marker_component = _component_number(paragraph.text)
        if marker_component is not None:
            component = marker_component

        text = paragraph.text.strip()
        if text.startswith("APPENDIX F. REFERENCES"):
            _set_text(paragraph, "APPENDIX E. REFERENCES")
            changed += 1
        elif text.startswith("APPENDIX E. STATUS AND VERIFICATION MATRIX"):
            _set_text(paragraph, "APPENDIX F. STATUS AND VERIFICATION MATRIX")
            changed += 1
        elif component == 43 and text == "ЛИЦЕНЗИЯ / LICENSE":
            _set_text(paragraph, "LICENSE AND COPYRIGHT")
            changed += 1
        elif component == 43 and re.search(r"[А-Яа-яЁё]", text) and " / " in text:
            english_text = text.rsplit(" / ", 1)[1].strip()
            if english_text:
                _set_text(paragraph, english_text)
                changed += 1
    return changed


def _update_shared_text(document, language: str) -> int:
    changed = 0
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("Лицензия / License:"):
            if language == "ru":
                _set_text(
                    paragraph,
                    "Лицензия: © 2026 Бугаенко Роман Сергеевич. Все права защищены. "
                    "Публичное чтение разрешено; иное использование — только с письменного согласия автора.",
                )
            else:
                _set_text(
                    paragraph,
                    "License: © 2026 Roman Sergeevich Bugaenko. All rights reserved. "
                    "Public reading is permitted; all other use requires the author's written permission.",
                )
            changed += 1
        elif language == "ru" and text.startswith("Содержание обновляется автоматически"):
            _set_text(
                paragraph,
                "Содержание обновляется автоматически: выделите весь документ и нажмите Ctrl+A, затем F9.",
            )
            changed += 1
        elif language == "ru" and text.startswith("Документ дополнен 23 "):
            _set_text(
                paragraph,
                "В публикацию включены 24 иллюстрации: схемы, графики и технические листы. "
                "Их числовые подписи согласованы с данными таблиц редакции 8; иллюстрации "
                "дополняют расчёты, но не заменяют отдельную верификацию модели.",
            )
            changed += 1
        elif language == "ru" and text.startswith("Редакционная отметка: рисунки 1–23"):
            _set_text(
                paragraph,
                "Редакционная отметка: комплект иллюстраций редакции 8 включает 24 рисунка; "
                "числовые подписи следует рассматривать вместе с таблицами и формулами "
                "документа. Иллюстрации не заменяют отдельную верификацию модели.",
            )
            changed += 1
        elif language == "en" and text.startswith("The document is supplemented with 23 "):
            _set_text(
                paragraph,
                "The Edition 8 publication includes 24 illustrations: diagrams, plots and technical sheets. "
                "Their numerical labels are aligned with the Edition 8 table data; they complement the "
                "calculations but do not replace independent model verification.",
            )
            changed += 1
        elif language == "en" and text.startswith("Editorial note: Figures 1–23"):
            _set_text(
                paragraph,
                "Editorial note: the Edition 8 illustration set comprises 24 figures. Read their numerical "
                "labels together with the document's tables and formulas; the figures do not replace "
                "independent model verification.",
            )
            changed += 1
    return changed


def prepare_document(language: str, path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    document = Document(path)
    _ensure_cover(document, language)
    changed = _update_shared_text(document, language)
    if language == "ru":
        changed += _translate_ru_labels_and_phrases(document)
    else:
        changed += _update_english_front_matter(document)
    removed = _remove_repeated_reference_blocks(document, language)

    temporary = path.with_name(path.stem + ".prepare.tmp.docx")
    document.save(temporary)
    temporary.replace(path)
    print(
        f"Prepared {path.relative_to(ROOT)}: {changed} text updates, "
        f"{removed} paragraphs removed from repeated section bibliographies."
    )


def main() -> int:
    for language, path in DOCS.items():
        prepare_document(language, path)
    print("PASS: Edition 8 covers, shared bibliography, and status matrix are prepared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
