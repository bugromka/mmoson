#!/usr/bin/env python3
"""Создаёт шаблон английского DOCX с переведёнными названиями разделов.
Текст разделов будет заполняться по частям в последующих шагах."""

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

OUT = Path("/home/user/mmoson/sections/MMOSON_combined_document_en.docx")

# Соответствие имён файлов к английским заголовкам
SECTION_TITLES = {
    "00_Аннотация": "Abstract",
    "00_ОГЛАВЛЕНИЕ": "Table of Contents",
    "00_Об_авторстве_и_методе_работы": "About Authors and Method of Work",
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

# Порядок файлов (такой же, как в русском)
import re
SRC = Path("/tmp/sections")
def sort_key(name: str) -> tuple:
    if name.startswith("00_"):
        return (0, name)
    match = re.match(r"(\d+)_", name)
    if match:
        return (1, int(match.group(1)), name)
    return (2, name)

files = sorted([p for p in SRC.glob("*.docx")], key=lambda p: sort_key(p.name))

doc = Document()
title = doc.add_heading("MMOSO'N — Combined Document (English Version)", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

sub = doc.add_paragraph(
    "Combination of all document sections of the MMOSO'N project. "
    "Source: sections/ directory of the bugromka/mmoson repository. "
    "English translation — in progress."
)
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

for fpath in files:
    stem = fpath.stem
    en_title = SECTION_TITLES.get(stem, stem)
    doc.add_heading(en_title, level=1)
    # Пустой абзац как заполнитель для текста (будет заменён переводом)
    doc.add_paragraph("")

doc.save(str(OUT))
print(f"Создан шаблон: {OUT}")
print(f"Разделов: {len(files)}")
