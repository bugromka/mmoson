#!/usr/bin/env python3
"""Собирает один самодостаточный HTML-файл сайта для встраивания в Google Sites.

Источник — site/index.html + css/styles.css + js/app.js + assets/fig/*.png.
Результат — site/mmoson-google-sites.html: стили, скрипт и все иллюстрации
внутри одного файла, без внешних файлов и без сетевых зависимостей
(кроме шрифтов Google Fonts, которые подгружаются с CDN и необязательны).

Иллюстрации перекодируются в WebP и встраиваются как data:URI.
Если Pillow недоступен, встраиваются исходные PNG — файл станет больше,
но сборка не сорвётся.

Запуск:
    python3 site/build_standalone.py
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CSS = ROOT / "css" / "styles.css"
JS = ROOT / "js" / "app.js"
OUT = ROOT / "mmoson-google-sites.html"
OUT_FRAGMENT = ROOT / "mmoson-google-sites-fragment.html"

MIME = {"webp": "image/webp", "png": "image/png"}


def encode_image(path: Path, max_width: int = 1000, quality: int = 78) -> tuple[str, int, int]:
    """Возвращает (data_uri, исходный_размер, итоговый_размер)."""
    raw = path.read_bytes()
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        data = base64.b64encode(raw).decode("ascii")
        return f"data:{MIME[path.suffix.lstrip('.')]};base64,{data}", len(raw), len(raw)

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    width, height = img.size
    if width > max_width:
        img = img.resize((max_width, round(height * max_width / width)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, method=6)
    packed = buf.getvalue()
    # WebP меньше PNG всегда; если вдруг нет — оставляем PNG
    if len(packed) >= len(raw):
        data = base64.b64encode(raw).decode("ascii")
        return f"data:{MIME[path.suffix.lstrip('.')]};base64,{data}", len(raw), len(raw)

    data = base64.b64encode(packed).decode("ascii")
    return f"data:image/webp;base64,{data}", len(raw), len(packed)


def to_fragment(html: str) -> str:
    """Тот же код без оболочки документа.

    Нужен, если Google Sites сам оборачивает вставленный код в документ и
    выбрасывает <head>. Тогда стили, шрифты и заголовок переезжают в начало
    <body> — браузер понимает их и там.
    """
    head_match = re.search(r"<head>(.*?)</head>", html, re.S)
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    if not head_match or not body_match:
        return html

    head = head_match.group(1)
    head = re.sub(r"<meta[^>]*>", "", head)
    head = head.replace("<title>ММОСО’Н — Модуль моделирования орбитальной станции О’Нила</title>", "")
    head = re.sub(r"<title>.*?</title>", "", head, flags=re.S)

    body = body_match.group(1)
    return head.strip() + "\n" + body.strip() + "\n"


def main() -> int:
    for path in (INDEX, CSS, JS):
        if not path.is_file():
            print(f"нет файла: {path}", file=sys.stderr)
            return 1

    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    # 1. Стили внутрь
    link_tag = '<link rel="stylesheet" href="css/styles.css">'
    if link_tag not in html:
        print("не найден тег подключения стилей", file=sys.stderr)
        return 1
    html = html.replace(link_tag, "<style>\n" + css + "\n</style>")

    # 2. Скрипт внутрь
    script_tag = '<script src="js/app.js"></script>'
    if script_tag not in html:
        print("не найден тег подключения скрипта", file=sys.stderr)
        return 1
    html = html.replace(script_tag, "<script>\n" + js + "\n</script>")

    # 3. Иллюстрации внутрь.
    # data-full="..." убираем: в одиночном файле полноразмерной служит сама
    # картинка карточки, иначе каждая иллюстрация попала бы в файл дважды.
    html = re.sub(r'\s+data-full="assets/fig/[^"]+"', "", html)
    images = sorted(set(re.findall(r"assets/fig/[A-Za-z0-9_\-.]+\.png", html)))
    raw_total = packed_total = 0
    for rel in images:
        src = ROOT / rel
        if not src.is_file():
            print(f"нет иллюстрации: {src}", file=sys.stderr)
            return 1
        uri, raw_size, packed_size = encode_image(src)
        raw_total += raw_size
        packed_total += packed_size
        html = html.replace(rel, uri)

    # 4. Метаданные сборки
    html = html.replace(
        "<head>",
        "<head>\n<!-- Собрано site/build_standalone.py: один файл для встраивания в Google Sites.\n"
        "     Внутри: стили, скрипт и иллюстрации. Отдельных файлов не требуется. -->",
        1,
    )

    OUT.write_text(html, encoding="utf-8")
    OUT_FRAGMENT.write_text(to_fragment(html), encoding="utf-8")
    left = re.findall(r'(?:src|href)="(?!https://|data:|#)([^"]+)"', html)
    size = OUT.stat().st_size
    print(f"готово: {OUT}")
    print(f"иллюстраций: {len(images)}, исходно {raw_total/1024:.0f} КБ → в файле {packed_total/1024:.0f} КБ")
    print(f"размер файла: {size/1024:.0f} КБ, символов: {len(html):,}".replace(",", " "))
    print(f"вариант без оболочки документа: {OUT_FRAGMENT.name} ({OUT_FRAGMENT.stat().st_size/1024:.0f} КБ)")
    print(f"остаточные локальные ссылки: {left if left else 'нет'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
