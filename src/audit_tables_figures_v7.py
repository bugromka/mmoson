# -*- coding: utf-8 -*-
"""Audit Edition 8 tables, captions and embedded figures.

This is an editorial consistency check, not an engineering certification. It
checks key table values and status wording, architecture constraints, figure
captions, embedded-image counts, per-language asset matching and PNG integrity.
Optional source PNGs are compared when present in src/fig; that legacy source
folder is not required in the current repository.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path
import hashlib
import io
import re
import sys
import zipfile

from docx import Document
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
from corpus import Corpus

DOC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sections"
FIG = ROOT / "src" / "fig"
errors: list[str] = []
notes: list[str] = []

D = Corpus(DOC)
# Each localized Edition 8 document contains the complete 24-sheet set.
CAPTIONS_EXPECTED = 24
IMAGES_EXPECTED = 2 * CAPTIONS_EXPECTED
TABLES_EXPECTED = {"ru": 69, "en": 67}

def fail(msg: str) -> None:
    errors.append(msg)

def norm(s: str) -> str:
    return " ".join(s.split())

def document_language(path: Path) -> str | None:
    if path.stem.endswith("_ru"):
        return "ru"
    if path.stem.endswith("_en"):
        return "en"
    return None

for path, document in zip(D.paths, D.docs):
    language = document_language(path)
    if language is None:
        fail(f"язык документа не определяется по имени файла: {path.name}")
    elif len(document.tables) != TABLES_EXPECTED[language]:
        fail(
            f"{path.name}: ожидалось {TABLES_EXPECTED[language]} таблиц редакции 8, "
            f"найдено {len(document.tables)}"
        )

def find_table(predicate, label: str):
    found = []
    for i, t in enumerate(D.tables, 1):
        text = "\n".join(norm(c.text) for r in t.rows for c in r.cells)
        if predicate(text):
            found.append((i, t, text))
    if not found:
        fail(f"не найдена таблица: {label}")
        return None
    return found[0]

def dnum(s: str) -> Decimal:
    s = s.replace(" ", "").replace(" ", "").replace(",", ".")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    if not m:
        raise ValueError(s)
    return Decimal(m.group(0))

# --- Table-level checks -------------------------------------------------
mass = find_table(lambda s: "ИТОГО СТАНЦИЯ" in s and "Ферменная рама по осям" in s,
                  "сводный массовый баланс")
if mass:
    _, t, _ = mass
    vals = {}
    for r in t.rows:
        label = norm(r.cells[0].text)
        if len(r.cells) >= 3:
            vals[label] = r.cells[2].text
    expected = Decimal("26.85") + Decimal("8.13") + Decimal("1.17") + Decimal("7.55") + Decimal("3.00")
    try:
        got = dnum(vals["ИТОГО СТАНЦИЯ"])
        if got != expected:
            fail(f"массовый баланс: {got} вместо {expected}")
    except Exception as exc:
        fail(f"массовый баланс не разобран: {exc}")

materials = find_table(lambda s: "Материал" in s and "Потребность, млрд т" in s and "Вода" in s,
                       "материальный баланс")
if materials:
    ti, t, text = materials
    required = ["Разработана на концептуальном уровне в главе 8",
                "промышленный график", "квалификация оборудования",
                "полномасштабные испытания"]
    for needle in required:
        if needle not in text:
            fail(f"таблица материального баланса (таблица {ti}): нет «{needle}»")
    try:
        total = sum(dnum(r.cells[1].text) for r in t.rows[1:])
        if total != Decimal("43.55"):
            fail(f"сумма материального баланса: {total} вместо 43.55")
    except Exception as exc:
        fail(f"материальный баланс не разобран: {exc}")

equip = find_table(lambda s: "Оборудование" in s and "44,675 млн т = 0,0447 млрд т" in s,
                   "ведомость оборудования осевого рамно-ферменного комплекса")
if equip:
    ti, t, text = equip
    if "концептуальная" not in text.lower() or "квалификация оборудования" not in text:
        fail(f"таблица оборудования {ti}: не зафиксирован концептуальный статус/квалификация")
    try:
        total = sum(dnum(r.cells[3].text) for r in t.rows[1:-1])
        if total != Decimal("44.675"):
            fail(f"детализация оборудования: {total} вместо 44.675 млн т")
    except Exception as exc:
        fail(f"детализация оборудования не разобрана: {exc}")

stages = find_table(lambda s: "Этап" in s and "Содержание работ" in s and "Соединение цилиндров" in s,
                    "этапы строительства")
if stages:
    text = stages[2]
    for needle in ["неподвижных осевых соединительных ферм", "продольного соединения боковых оболочек нет"]:
        if needle not in text:
            fail(f"этапы строительства: нет «{needle}»")
    if "Монтаж внешнего соединения и подшипниковых узлов" in text:
        fail("вернулась старая формулировка внешнего/продольного соединения")

transport = find_table(lambda s: "Заселение 500 000 чел. по транспорту" in s,
                       "сводка транспортного заселения")
if transport:
    text = transport[2]
    for needle in ["15,4 суток на цилиндр", "7,7 суток на станцию", "2 700 чел./ч"]:
        if needle not in text:
            fail(f"сводка транспортного заселения: нет «{needle}»")

strength = find_table(lambda s: "18Ni(300)" in s and "Допускаемое σ" in s,
                      "таблица материалов силового пояса")
if strength and not any("запас 1,53" in norm(c.text) for t in D.tables for r in t.rows for c in r.cells):
    fail("документ не содержит канонический коэффициент запаса 1,53")

# --- Caption/image checks -----------------------------------------------
caption_nums = []
for p in D.paragraphs:
    m = re.match(r"Рисунок\s+(\d+)\s+—", norm(p.text))
    if m:
        caption_nums.append(int(m.group(1)))
if caption_nums != list(range(1, CAPTIONS_EXPECTED + 1)):
    fail(f"подписи рисунков: ожидался ряд 1..{CAPTIONS_EXPECTED}, "
         f"получено {caption_nums}")
if len(D.inline_shapes) != IMAGES_EXPECTED:
    fail(f"встроенные рисунки: ожидалось {IMAGES_EXPECTED} "
         f"(русская и английская редакции), найдено {len(D.inline_shapes)}")

# Each document must embed the exact artwork set for its language. The
# Russian and English media are expected to have different hashes.
asset_dirs = {
    "ru": ROOT / "site" / "assets" / "fig_ru",
    "en": ROOT / "site" / "assets" / "fig_en",
}
all_hashes = set()
for path in D.paths:
    language = document_language(path)
    if language is None:
        fail(f"язык документа не определяется по имени файла: {path.name}")
        continue
    asset_dir = asset_dirs[language]
    expected_files = sorted(asset_dir.glob("fig*.png"))
    if len(expected_files) != CAPTIONS_EXPECTED:
        fail(f"{language}: ожидалось {CAPTIONS_EXPECTED} локализованных PNG в {asset_dir}, "
             f"найдено {len(expected_files)}")
    expected_hashes = Counter(hashlib.sha256(source.read_bytes()).hexdigest() for source in expected_files)

    with zipfile.ZipFile(path) as z:
        media_names = [
            name for name in z.namelist()
            if name.startswith("word/media/") and name.lower().endswith(".png")
        ]
        embedded_hashes = Counter(hashlib.sha256(z.read(name)).hexdigest() for name in media_names)
    all_hashes.update(embedded_hashes)
    if len(media_names) != CAPTIONS_EXPECTED:
        fail(f"{path.name}: ожидалось {CAPTIONS_EXPECTED} встроенных PNG, найдено {len(media_names)}")
    if embedded_hashes != expected_hashes:
        missing = list((expected_hashes - embedded_hashes).elements())
        extra = list((embedded_hashes - expected_hashes).elements())
        fail(f"{path.name}: набор встроенных рисунков не совпадает с {asset_dir.name}; "
             f"отсутствуют {len(missing)}, лишние {len(extra)}")
for source_name in ["fig09_thermal.png", "fig16_resources.png", "fig21_volatiles.png"]:
    source = FIG / source_name
    if not source.exists():
        notes.append(f"не найден необязательный исходник {source_name}; сравнение с исходником пропущено")
        continue
    src_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if src_hash not in all_hashes:
        fail(f"эталонный рисунок {source_name} не встроен ни в один документ")
    try:
        with Image.open(source) as im:
            if im.width < 500 or im.height < 250:
                fail(f"слишком маленький рисунок {source_name}: {im.size}")
    except Exception as exc:
        fail(f"не читается рисунок {source_name}: {exc}")

# Проверяем целостность каждого встроенного PNG без необходимости хранить
# отдельные исходники рисунков в репозитории.
for path in D.paths:
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not (name.startswith("word/media/") and name.lower().endswith(".png")):
                continue
            try:
                with Image.open(io.BytesIO(z.read(name))) as image:
                    image.load()
                    if image.width < 500 or image.height < 250:
                        fail(f"слишком маленький встроенный рисунок {path.name}:{name}: {image.size}")
            except Exception as exc:
                fail(f"не читается встроенный рисунок {path.name}:{name}: {exc}")

# Text-level architecture guard.
all_text = "\n".join(norm(p.text) for p in D.paragraphs)
all_text += "\n" + "\n".join(norm(c.text) for t in D.tables for r in t.rows for c in r.cells)
for needle in ["Оборудование на боковой обшивке", "оборудование не закрепляется на вращающейся оболочке",
               "боковые оболочки между собой не соединены", "Продольной конструкции вдоль межцилиндрового зазора нет"]:
    if needle not in all_text:
        fail(f"архитектурная оговорка отсутствует: {needle}")

print("=" * 76)
print("АВТОМАТИЧЕСКАЯ СВЕРКА ТАБЛИЦ, ПОДПИСЕЙ И РИСУНКОВ · РЕДАКЦИЯ 8")
print("=" * 76)
print(f"Документ: {DOC}")
print(f"Абзацев: {len(D.paragraphs)}; таблиц: {len(D.tables)}; рисунков: {len(D.inline_shapes)}")
if errors:
    print("ОШИБКИ:")
    for e in errors:
        print("  -", e)
    print(f"Результат: FAIL ({len(errors)} ошибок)")
    raise SystemExit(1)
print("Сводные суммы, статусы, архитектурные ограничения, подписи и встроенные рисунки согласованы.")
if notes:
    print("ПРИМЕЧАНИЯ:")
    for note in notes:
        print("  -", note)
print("Результат: PASS")
