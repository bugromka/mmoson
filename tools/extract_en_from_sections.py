#!/usr/bin/env python3
"""Извлекает английский текст из каждого раздела DOCX и записывает в общий английский DOCX.
В исходных файлах английский текст идет после маркера 'ENGLISH EDITION'."""

from docx import Document
from pathlib import Path
import re
import sys

SRC_RU = Path("/tmp/sections")
DST_EN = Path("/home/user/mmoson/sections/MMOSON_combined_document_en.docx")

SECTION_TITLES = {
    "00_Аннотация": "Abstract",
    "00_ОГЛАВЛЕНИЕ": "Table of Contents",
    "00_Об_авторстве_и_методе_работы": "About Authorship and Work Method",
    "01_Введение_Концепция_проекта": "Introduction. Project Concept",
    "02_Физические_принципы_и_расчётные_параметры": "Physical Principles and Calculation Parameters",
    "03_Биоразнообразие_и_зональное_распределение": "Biodiversity and Zonal Distribution",
    "04_Инженерные_и_конструктивные_решения": "Engineering and Design Solutions",
    "05_Продовольственный_баланс_и_эффективность_биосферы": "Food Balance and Biosphere Efficiency",
    "06_Средообразование": "Environmental Formation",
    "07_Человек_в_замкнутой_среде": "Human in a Closed Environment",
    "08_Программа_добычи_летучих_и_воды": "Volatiles and Water Extraction Program",
    "09_Карантинный_контур": "Quarantine Circuit",
    "10_Изготовление_и_монтаж_оболочки": "Shell Manufacturing and Installation",
    "11_Дополнительные_инженерные_вопросы": "Additional Engineering Issues",
    "12_Внутренняя_среда": "Internal Environment",
    "13_Правовые_основы_программы": "Legal Basis of the Program",
    "14_Аварийные_режимы_и_ресурс_конструкции": "Emergency Modes and Structural Resource",
    "15_Почвенная_биота_психология_экономика": "Soil Biota, Psychology, Economics",
    "16_Кислородный_баланс_во_времени": "Oxygen Balance Over Time",
    "17_Правоохранительная_и_социальная_система": "Law Enforcement and Social System",
    "18_Ядерная_и_термоядерная_энергетика": "Nuclear and Thermonuclear Energy",
    "19_Сводка_дополнительных_нерешённых_задач": "Summary of Additional Unresolved Tasks",
    "20_Носовые_купола_как_ограничение_давления": "Nose Domes as a Pressure Boundary",
    "21_Аварийная_потеря_вращения": "Emergency Loss of Rotation",
    "22_Визуальная_среда_замкнутого_мира": "Visual Environment of a Closed World",
    "23_Химия_воздуха_на_столетия": "Air Chemistry for Centuries",
    "24_Почва_как_инженерный_профиль": "Soil as an Engineering Profile",
    "25_Масштабирование_архитектуры": "Architecture Scaling",
    "26_Связь_с_Землёй_из_точки_L1": "Communication with Earth from L1 Point",
    "27_Сводка_новых_областей": "Summary of New Areas",
    "28_Генетика_замкнутой_популяции": "Genetics of a Closed Population",
    "29_Сельское_хозяйство_пересмотр_и_оптимизация": "Agriculture Review and Optimization",
    "30_Промышленность_добыча_переработка_отходы": "Industry, Extraction, Processing, Waste",
    "31_Стыковочный_модуль_концепция": "Docking Module Concept",
    "32_Кошки_в_экосистеме": "Cats in the Ecosystem",
    "33_Насекомые_опылители_разлагатели_кормовая_база": "Insects, Pollinators, Decomposers, Feed Base",
    "34_Города_реальные_и_виртуальные": "Real and Virtual Cities",
    "ЛИЦЕНЗИЯ": "LICENCE",
    "ПРИЛОЖЕНИЕ_Б_Обоснование_расчётов": "Appendix B. Calculation Substantiation",
    "ПРИЛОЖЕНИЕ_В_Перечень_сокращений_и_обозначений": "Appendix C. List of Abbreviations and Symbols",
    "ПРИЛОЖЕНИЕ_Г_Источники": "Appendix D. Sources",
    "ПРИЛОЖЕНИЕ_Д_Список_использованной_литературы": "Appendix E. Bibliography",
    "ПРИЛОЖЕНИЕ_Е_Матрица_статусов_и_проверок": "Appendix F. Status and Check Matrix",
}

def sort_key(name: str) -> tuple:
    if name.startswith("00_"):
        return (0, name)
    match = re.match(r"(\d+)_", name)
    if match:
        return (1, int(match.group(1)), name)
    return (2, name)

def extract_en_text(fpath: Path) -> str:
    """Извлекает английскую часть из DOCX файла — всё после 'ENGLISH EDITION' до конца."""
    doc = Document(str(fpath))
    paragraphs = [p.text for p in doc.paragraphs]
    
    # Находим маркер ENGLISH EDITION
    en_start = None
    for i, text in enumerate(paragraphs):
        if "ENGLISH EDITION" in text.upper():
            en_start = i + 1
            break
    
    if en_start is None:
        return ""
    
    # Берём всё после маркера, до 'СПИСОК ЛИТЕРАТУРЫ РАЗДЕЛА' или до конца
    en_parts = []
    for text in paragraphs[en_start:]:
        if text.strip():
            en_parts.append(text)
    
    return "\n".join(en_parts)

def fill_all_en() -> None:
    files = sorted([p for p in SRC_RU.glob("*.docx")], key=lambda p: sort_key(p.name))
    
    doc_en = Document(str(DST_EN))
    
    # Удаляем существующие пустые абзацы после заголовков (кроме первого после заголовка документа)
    # Пересоздаём документ с правильной структурой
    new_doc = Document()
    
    title = new_doc.add_heading("MMOSON — Combined Document (English Version)", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    sub = new_doc.add_paragraph(
        "Combination of all document sections of the MMOSON project. "
        "Source: sections/ directory of the bugromka/mmoson repository. "
        "English text extracted from the original bilingual DOCX files."
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    total_chars = 0
    for i, fpath in enumerate(files, 1):
        stem = fpath.stem
        en_title = SECTION_TITLES.get(stem, stem)
        en_text = extract_en_text(fpath)
        
        print(f"[{i:2d}/{len(files)}] {stem} -> {en_title} ({len(en_text)} chars)")
        
        new_doc.add_heading(en_title, level=1)
        
        if en_text.strip():
            # Разбиваем на абзацы
            for para_text in en_text.split("\n"):
                if para_text.strip():
                    new_doc.add_paragraph(para_text)
            total_chars += len(en_text)
        else:
            new_doc.add_paragraph("")
            print(f"  WARNING: английский текст не найден")
    
    new_doc.save(str(DST_EN))
    print(f"\nСохранено: {DST_EN}")
    print(f"Всего английских символов: {total_chars:,}")

if __name__ == "__main__":
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    fill_all_en()
