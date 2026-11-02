#!/usr/bin/env python3
"""Объединяет все DOCX из /tmp/sections/ в один DOCX (русская версия)."""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
import re

SRC = Path("/tmp/sections")
OUT = Path("/home/user/mmoson/sections_combined_ru.docx")

# Порядок файлов: сначала 00-*, poi 01-34, потом приложения
def sort_key(name: str) -> tuple:
    """Сортировка: 00_* первыми, потом по номеру, потом приложения в конце."""
    if name.startswith("00_"):
        return (0, name)
    match = re.match(r"(\d+)_", name)
    if match:
        return (1, int(match.group(1)), name)
    # Приложения и прочие — в конце
    return (2, name)


def main() -> None:
    files = sorted([p for p in SRC.glob("*.docx")], key=lambda p: sort_key(p.name))
    print(f"Найдено файлов: {len(files)}")

    combined = Document()

    # Заголовок документа
    title = combined.add_heading("ММОСО'Н — Объединённый документ (русская версия)", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = combined.add_paragraph(
        "Объединение всех разделов документа проекта ММОСО'Н. "
        "Источник: папка sections/ репозитория bugromka/mmoson."
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    total_chars = 0
    for i, fpath in enumerate(files, 1):
        print(f"[{i:2d}/{len(files)}] {fpath.name}")
        doc = Document(str(fpath))

        # Заголовок раздела (имя файла без расширения)
        section_title = fpath.stem
        h = combined.add_heading(section_title, level=1)

        # Добавляем абзацы
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            # Копируем стиль и форматирование
            new_para = combined.add_paragraph()
            for run in para.runs:
                new_run = new_para.add_run(run.text)
                new_run.bold = run.bold
                new_run.italic = run.italic
                if run.font.size:
                    new_run.font.size = run.font.size
                if run.font.color and run.font.color.rgb:
                    new_run.font.color.rgb = run.font.color.rgb
            new_para.alignment = para.alignment
            total_chars += len(para.text)

        # Разделитель между разделами
        combined.add_paragraph("")

    combined.save(str(OUT))
    print(f"\nСохранено: {OUT}")
    print(f"Всего символов: {total_chars:,}")


if __name__ == "__main__":
    main()
