#!/usr/bin/env python3
"""Заполняет перевод в английском DOCX по указанным разделам.
Использование: python3 tools/fill_en_translation.py <номер_раздела_1> <номер_раздела_2> ...
"""

from docx import Document
from pathlib import Path
import re
import sys

SRC_RU = Path("/tmp/sections")
DST_EN = Path("/home/user/mmoson/sections/MMOSON_combined_document_en.docx")

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

def sort_key(name: str) -> tuple:
    if name.startswith("00_"):
        return (0, name)
    match = re.match(r"(\d+)_", name)
    if match:
        return (1, int(match.group(1)), name)
    return (2, name)

def extract_ru_text(fpath: Path) -> str:
    doc = Document(str(fpath))
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    return "\n".join(parts)

def fill_translation(section_indices: list[int]) -> None:
    files = sorted([p for p in SRC_RU.glob("*.docx")], key=lambda p: sort_key(p.name))
    
    doc_en = Document(str(DST_EN))
    
    for idx in section_indices:
        if idx < 1 or idx > len(files):
            print(f"Пропуск {idx}: вне диапазона 1-{len(files)}")
            continue
        
        fpath = files[idx - 1]
        stem = fpath.stem
        en_title = SECTION_TITLES.get(stem, stem)
        ru_text = extract_ru_text(fpath)
        
        print(f"[{idx:2d}/{len(files)}] {stem} -> {en_title} ({len(ru_text)} chars)")
        
        # Находим заголовок в английском документе и заменяет следующий пустой абзац
        found = False
        for i, para in enumerate(doc_en.paragraphs):
            if para.text == en_title and para.style.name == "Heading 1":
                # Ищем следующий пустой абзац после заголовка
                for j in range(i + 1, len(doc_en.paragraphs)):
                    if not doc_en.paragraphs[j].text.strip():
                        # Очищаем и добавляем перевод
                        p = doc_en.paragraphs[j]
                        # Удаляем все run'ы
                        for run in list(p.runs):
                            run.text = ""
                        # Добавляем перевод как абзацы
                        # Разбиваем текст на абзацы по пустым строкам
                        ru_paras = [ptext for ptext in ru_text.split("\n") if ptext.strip()]
                        first = True
                        for ru_p in ru_paras:
                            if first:
                                p.text = ru_p  # используем первый пустой абзац
                                first = False
                            else:
                                new_p = doc_en.add_paragraph()
                                # Вставляем после текущего заголовка
                                doc_en._element.body.insert(
                                    list(doc_en._element.body).index(p._element) + 1,
                                    new_p._element
                                )
                                new_p.text = ru_p
                        found = True
                        break
                break
        
        if not found:
            print(f"  WARNING: заголовок '{en_title}' не найден в английском документе")

    doc_en.save(str(DST_EN))
    print(f"\nСохранено: {DST_EN}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 tools/fill_en_translation.py <номер_раздела> [номер_раздела ...]")
        print("Пример: python3 tools/fill_en_translation.py 1 2 3")
        sys.exit(1)
    
    indices = [int(x) for x in sys.argv[1:]]
    fill_translation(indices)
