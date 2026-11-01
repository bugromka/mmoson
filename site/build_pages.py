#!/usr/bin/env python3
"""Собирает многостраничный сайт ММОСО’Н.

Каждая страница — один самодостаточный HTML-файл: разметка, весь CSS,
весь JS и только её собственные иллюстрации (data:image/webp) внутри.
Отдельные css/, js/ и картинки во время работы страницы не нужны.

Собираются ДВА набора из одних и тех же исходников:

  site/<page>.html   версия для хостинга и локального просмотра:
                     с шапкой-меню и переходами «назад / дальше».

  site/embed/<page>.html
                     версия для встраивания в Google Sites:
                     без шапки и без переходов, потому что навигацию даёт
                     меню самого Sites. Внутренние ссылки сведены к href="#"
                     и оживают только если заполнить карту адресов
                     window.MMOSON_LINKS (см. комментарий в файле).

Источники:
  content/<page>.html   разметка страницы без обвязки
  css/styles.css        общий стиль
  js/app.js             общее поведение
  assets/fig/*.png      иллюстрации в исходном разрешении

Запуск:
    python3 site/build_pages.py
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
CSS = ROOT / "css" / "styles.css"
JS = ROOT / "js" / "app.js"
EMBED = ROOT / "embed"

PAGES = [
    {
        "slug": "index",
        "nav": "Главная",
        "title": "ММОСО’Н — Модуль моделирования орбитальной станции О’Нилла",
        "desc": "Расчётная модель обитаемой орбитальной станции О’Нилла в точке L1: два встречновращающихся цилиндра, 1 000 000 жителей, полный инженерный и биосферный баланс.",
        "kicker": "",
        "h1": "",
        "sub": "",
        "page_head": False,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "engineering",
        "nav": "Инженерия",
        "title": "Инженерные решения — ММОСО’Н",
        "desc": "Оболочка и её прочность, теплосброс двумя контурами, энергетика, транспорт «ось — обод», причал и шлюзы, биосфера станции.",
        "kicker": "Конструкция и системы",
        "h1": "Инженерные решения",
        "sub": "Шесть контуров станции: каждый замкнут на расчёт, а не на иллюстрацию.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "verification",
        "nav": "Верификация",
        "title": "Расчётная верификация — ММОСО’Н",
        "desc": "243/243 независимых пересчёта, сверка корпуса публикации, ноль дефектов вёрстки, запас прочности 1,53 и открытые задачи проекта.",
        "kicker": "Проверки и открытые задачи",
        "h1": "Расчётная верификация",
        "sub": "Каждая проверка воспроизводится одной командой: код лежит рядом с документом.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "gallery",
        "nav": "Иллюстрации",
        "title": "Иллюстрации — ММОСО’Н",
        "desc": "Восемь листов из публикации: компоновка станции, сечение и обшивка, трасса «ось — обод», энергия, климат, ресурсы, продовольствие, землепользование.",
        "kicker": "Листы публикации",
        "h1": "Иллюстрации",
        "sub": "Восемь технических листов проекта. Нажмите на лист, чтобы открыть крупно.",
        "page_head": True,
        "img": {"max_width": 1080, "quality": 78},
    },
    {
        "slug": "edition",
        "nav": "Издание",
        "title": "Издание — ММОСО’Н",
        "desc": "43 документа, 34 раздела, две языковые редакции, приложения с обоснованием расчётов и матрицей проверок.",
        "kicker": "Публикация",
        "h1": "Издание",
        "sub": "43 документа, 34 раздела, русская и английская редакции.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "contacts",
        "nav": "Контакты",
        "title": "Контакты — ММОСО’Н",
        "desc": "Связаться с автором проекта ММОСО’Н: почта, Макс, ВКонтакте, Добро.рф. Реквизиты проекта, статус, адрес и порядок цитирования.",
        "kicker": "",
        "h1": "",
        "sub": "",
        "page_head": False,
        "shell": False,
        "css": "css/contacts.css",
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "authors",
        "nav": "Авторы",
        "title": "Авторы и лицензия — ММОСО’Н",
        "desc": "Автор проекта, расчётная линия НИК, условия использования материалов и порядок ссылки на публикацию.",
        "kicker": "Люди и права",
        "h1": "Авторы и лицензия",
        "sub": "Человек и расчётная линия. Чтение открыто, использование — по согласию.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
]

MARK = """<svg class="nav-mark" viewBox="0 0 48 48" aria-hidden="true">
        <circle cx="24" cy="15" r="8" fill="none" stroke="currentColor" stroke-width="2.6"/>
        <circle cx="24" cy="33" r="8" fill="none" stroke="currentColor" stroke-width="2.6"/>
        <line x1="24" y1="6" x2="24" y2="42" stroke="currentColor" stroke-width="1.4" stroke-dasharray="2 4" opacity=".7"/>
      </svg>"""


def link(page: dict, active: str, embed: bool) -> tuple[str, str]:
    """Адрес и дополнительные атрибуты ссылки на страницу."""
    if embed:
        return "#", f' class="active"' if page["slug"] == active else ""
    return f'{page["slug"]}.html', ' class="active"' if page["slug"] == active else ""


def nav_html(active: str, embed: bool) -> str:
    if embed:
        return ""
    items = []
    for page in PAGES:
        href, cls = link(page, active, False)
        items.append(f'      <li><a href="{href}" data-page="{page["slug"]}"{cls}>{page["nav"]}</a></li>')
    return (
        '<header class="nav-wrap">\n'
        '  <nav class="nav" aria-label="Основная навигация">\n'
        '    <a href="index.html" data-page="index" class="nav-brand">\n'
        f"      {MARK}\n      <span>ММОСО’Н</span>\n    </a>\n"
        '    <button class="nav-toggle" aria-expanded="false" aria-controls="nav-links" aria-label="Меню">\n'
        "      <span></span><span></span><span></span>\n"
        "    </button>\n"
        '    <ul class="nav-links" id="nav-links">\n' + "\n".join(items) + "\n    </ul>\n  </nav>\n</header>"
    )


def page_head_html(page: dict) -> str:
    if not page["page_head"]:
        return ""
    return (
        '<section class="page-head">\n'
        '  <div class="container">\n'
        f'    <p class="eyebrow">{page["kicker"]}</p>\n'
        f'    <h1>{page["h1"]}</h1>\n'
        f'    <p class="page-sub">{page["sub"]}</p>\n'
        "  </div>\n"
        "</section>"
    )


def pager_html(slug: str, embed: bool) -> str:
    if embed:
        return ""
    idx = next(i for i, p in enumerate(PAGES) if p["slug"] == slug)
    prev_page = PAGES[idx - 1] if idx > 0 else None
    next_page = PAGES[idx + 1] if idx + 1 < len(PAGES) else None
    left = (
        f'  <a class="pager-prev" href="{prev_page["slug"]}.html" data-page="{prev_page["slug"]}">\n'
        '    <span class="pager-label">Назад</span>\n'
        f'    <span class="pager-name">← {prev_page["nav"]}</span>\n  </a>'
        if prev_page
        else "  <span></span>"
    )
    right = (
        f'  <a class="pager-next" href="{next_page["slug"]}.html" data-page="{next_page["slug"]}">\n'
        '    <span class="pager-label">Дальше</span>\n'
        f'    <span class="pager-name">{next_page["nav"]} →</span>\n  </a>'
        if next_page
        else "  <span></span>"
    )
    return '<nav class="pager" aria-label="Переход между страницами">\n' + left + "\n" + right + "\n</nav>"


def encode_image(path: Path, max_width: int = 1200, quality: int = 80) -> tuple[str, int]:
    raw = path.read_bytes()
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}", len(raw)

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    width, height = img.size
    if width > max_width:
        img = img.resize((max_width, round(height * max_width / width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, method=6)
    packed = buf.getvalue()
    if len(packed) >= len(raw):
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}", len(raw)
    return f"data:image/webp;base64,{base64.b64encode(packed).decode('ascii')}", len(packed)


def embed_links(html: str) -> str:
    """В embed-версии относительные переходы заменяются на href="#" + data-page."""
    def repl(match: re.Match[str]) -> str:
        slug = match.group(1)
        tail = match.group(2)
        # data-page уже стоит в ссылке — второй раз не добавляем
        attr = "" if "data-page" in tail else f' data-page="{slug}"'
        return f'href="#"{attr}'

    return re.sub(r'href="(?!https://|data:|#)([a-z]+)\.html"([^>]*)', repl, html)


def build(page: dict, css: str, js: str, embed: bool) -> tuple[str, int]:
    fragment = (CONTENT / f'{page["slug"]}.html').read_text(encoding="utf-8").strip()
    shell = page.get("shell", True)

    if not shell:
        # Страница-визитка со своим оформлением: без общей шапки, переходов и
        # подвала — только содержимое в контейнере, как в образце.
        body = '<div class="container">\n' + fragment + "\n</div>"
        return finish(page, body, css, js, embed)

    parts = []
    # Навигация, пагинатор и подвал убраны со всех страниц —
    # навигация и подвал делаются в меню Google Sites.
    parts.append('<main class="page" id="top">')
    head_block = page_head_html(page)
    if head_block:
        parts.append(head_block)
    parts.append(fragment)
    parts.append("</main>")
    body = "\n\n".join(parts)

    return finish(page, body, css, js, embed)


def finish(page: dict, body: str, css: str, js: str, embed: bool) -> tuple[str, int]:
    mode_note = ""
    if not page.get("shell", True):
        mode_note = " Страница-визитка: своя таблица стилей, без общей шапки и подвала. Навигация — меню сайта."
    elif embed:
        mode_note = " Версия для встраивания в Google Sites: навигация — меню самого Sites. Внутренние ссылки ведут на href=\"#\"."
    else:
        mode_note = " Версия для хостинга: переходы между страницами относительные."

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page["title"]}</title>
<meta name="description" content="{page["desc"]}">
<meta name="theme-color" content="#8f7ed6">
<!-- ММОСО’Н · страница «{page["nav"]}». Один самодостаточный файл: разметка, стили, скрипт и иллюстрации внутри. {mode_note} -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Raleway:wght@300;400;500;600;700&display=swap">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%238f7ed6'/%3E%3Ccircle cx='32' cy='24' r='9' fill='none' stroke='%23fff' stroke-width='3'/%3E%3Ccircle cx='32' cy='44' r='9' fill='none' stroke='%23fff' stroke-width='3'/%3E%3C/svg%3E">
<style>
{css}
</style>
<noscript><style>.fade-in{{opacity:1!important;transform:none!important}}</style></noscript>
</head>
<body>

{body}

<script>
{js}
</script>
</body>
</html>
"""

    html = embed_links(html)

    settings = page.get("img", {})
    inlined = 0
    for rel in sorted(set(re.findall(r"assets/fig/[A-Za-z0-9_\-.]+\.png", html))):
        uri, size = encode_image(
            ROOT / rel,
            max_width=settings.get("max_width", 1200),
            quality=settings.get("quality", 80),
        )
        inlined += size
        html = html.replace(rel, uri)

    return html, inlined


def main() -> int:
    default_css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    EMBED.mkdir(exist_ok=True)
    print(f"стили: {len(default_css)/1024:.0f} КБ · скрипт: {len(js)/1024:.0f} КБ\n")

    rows = []
    for page in PAGES:
        css_path = ROOT / page.get("css", "css/styles.css")
        css = css_path.read_text(encoding="utf-8")
        for embed, folder in ((False, ROOT), (True, EMBED)):
            html, inlined = build(page, css, js, embed)
            out = folder / f'{page["slug"]}.html'
            out.write_text(html, encoding="utf-8")
            left = [
                x
                for x in re.findall(r'(?:src|href)="(?!https://|data:|#|mailto:|tel:)([^"]+)"', html)
                if not x.endswith(".html")
            ]
            rows.append((str(out.relative_to(ROOT)), out.stat().st_size, inlined, left, len(html)))

    for name, size, inlined, left, chars in rows:
        note = f"  ⚠ локальные ссылки: {left}" if left else ""
        print(f"{name:<24} {size/1024:6.0f} КБ  иллюстраций {inlined/1024:5.0f} КБ  символов {chars:>7,}{note}".replace(",", " "))

    total = sum(r[1] for r in rows)
    print(f"\nвсего {len(rows)} файлов, {total/1024/1024:.2f} МБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
