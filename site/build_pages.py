#!/usr/bin/env python3
"""Собирает многостраничный сайт ММОСО’Н.

Каждая страница — один самодостаточный HTML-файл: разметка, весь CSS,
весь JS и только её собственные иллюстрации (data:image/webp) внутри.
Отдельные css/, js/ и картинки во время работы страницы не требуются.

Страницы распределяются по языковым папкам:

  site/ru/<page>.html   русская версия
  site/en/<page>.html   английская версия

Источники:
  content/<page>.html   разметка страницы без обвязки
  css/styles.css        общий стиль
  js/app.js             общее поведение
  assets/fig_ru/*.png и assets/fig_en/*.png      иллюстрации галерей

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
RU_DIR = ROOT / "ru"
EN_DIR = ROOT / "en"
PUBLISH_RU_DIR = ROOT.parent / "ru"
PUBLISH_EN_DIR = ROOT.parent / "en"

PAGES = [
    {
        "slug": "index",
        "lang": "ru",
        "output": "index.html",
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
        "slug": "index-en",
        "lang": "en",
        "output": "index.html",
        "nav": "Home",
        "title": "MMOSO'N — O'Neill Station Modeling Module",
        "desc": "Calculable model of a habitable O'Neill orbital station at L1 point: two counter-rotating cylinders, 1,000,000 inhabitants, full engineering and biosphere balance.",
        "kicker": "",
        "h1": "",
        "sub": "",
        "page_head": False,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "engineering",
        "lang": "ru",
        "output": "engineering.html",
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
        "slug": "engineering-en",
        "lang": "en",
        "output": "engineering.html",
        "nav": "Engineering",
        "title": "Engineering — MMOSO'N",
        "desc": "Shell and its strength, dual-loop heat rejection, power, axis-to-rim transport, docking and locks, station biosphere.",
        "kicker": "Construction and systems",
        "h1": "Engineering",
        "sub": "Six station circuits: each closed on calculation, not illustration.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "verification",
        "lang": "ru",
        "output": "verification.html",
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
        "slug": "verification-en",
        "lang": "en",
        "output": "verification.html",
        "nav": "Verification",
        "title": "Calculation Verification — MMOSO'N",
        "desc": "243/243 independent recalculations, publication cross-check, zero layout defects, safety margin 1.53 and open project tasks.",
        "kicker": "Checks and open tasks",
        "h1": "Calculation Verification",
        "sub": "Each check is reproducible by one command: code is next to the document.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "gallery",
        "lang": "ru",
        "output": "gallery.html",
        "nav": "Иллюстрации",
        "title": "Иллюстрации — ММОСО’Н",
        "desc": "24 технических листа проекта: компоновка станции, инженерные системы, ресурсы, климат, продовольствие, карантин и конструкция панелей.",
        "kicker": "Листы публикации",
        "h1": "Иллюстрации",
        "sub": "Все 24 технических листа проекта. Нажмите на изображение, чтобы открыть крупно.",
        "page_head": True,
        "img": {"max_width": 1080, "quality": 78},
    },
    {
        "slug": "gallery-en",
        "lang": "en",
        "output": "gallery.html",
        "nav": "Gallery",
        "title": "Illustrations — MMOSO'N",
        "desc": "Twenty-four technical illustrations covering station layout, engineering, climate, transport, food, resources, and operations.",
        "kicker": "Publication sheets",
        "h1": "Illustrations",
        "sub": "All 24 technical sheets of the project. Click any image to view it full size.",
        "page_head": True,
        "img": {"max_width": 1080, "quality": 78},
    },
    {
        "slug": "edition",
        "lang": "ru",
        "output": "edition.html",
        "nav": "Издание",
        "title": "Издание — ММОСО’Н",
        "desc": "Редакция 8: 34 раздела собраны в один объединённый DOCX на каждом языке, вместе с приложениями и вводными материалами.",
        "kicker": "Публикация",
        "h1": "Издание",
        "sub": "Редакция 8 · 34 раздела · два объединённых DOCX-файла.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "edition-en",
        "lang": "en",
        "output": "edition.html",
        "nav": "Edition",
        "title": "Edition — MMOSO'N",
        "desc": "Edition 8: 34 sections consolidated into one DOCX per language, including the front matter and appendices.",
        "kicker": "Publication",
        "h1": "Edition",
        "sub": "Edition 8 · 34 sections · two combined DOCX files.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "contacts",
        "lang": "ru",
        "output": "contacts.html",
        "nav": "Контакты",
        "title": "Контакты — ММОСО’Н",
        "desc": "Связаться с автором проекта ММОСО’Н: почта, Макс, ВКонтакте, Добро.рф. Реквизиты проекта, статус, адрес и порядок цитирования.",
        "kicker": "",
        "h1": "",
        "sub": "",
        "page_head": False,
        "shell": True,
        "pager": True,
        "wrap_content": True,
        "css": ["css/styles.css", "css/contacts.css"],
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "contacts-en",
        "lang": "en",
        "output": "contacts.html",
        "nav": "Contacts",
        "title": "Contacts — MMOSO'N",
        "desc": "Contact the author of the MMOSO'N project: email, Max, VK, Dobro.ru. Project details, status, address and citation procedure.",
        "kicker": "",
        "h1": "",
        "sub": "",
        "page_head": False,
        "shell": True,
        "pager": True,
        "wrap_content": True,
        "css": ["css/styles.css", "css/contacts.css"],
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "authors",
        "lang": "ru",
        "output": "authors.html",
        "nav": "Авторы",
        "title": "Авторы и лицензия — ММОСО’Н",
        "desc": "Автор проекта, расчётная линия НИК, условия использования материалов и порядок ссылки на публикацию.",
        "kicker": "Люди и права",
        "h1": "Авторы и лицензия",
        "sub": "Человек и расчётная линия. Чтение открыто, использование — по согласию.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
    {
        "slug": "authors-en",
        "lang": "en",
        "output": "authors.html",
        "nav": "Authors",
        "title": "Authors and License — MMOSO'N",
        "desc": "Project author, calculation line NIK, terms of material use and citation procedure.",
        "kicker": "People and rights",
        "h1": "Authors and License",
        "sub": "Person and calculation line. Reading open, use — by agreement.",
        "page_head": True,
        "img": {"max_width": 1200, "quality": 82},
    },
]

LOGO_ASSETS = {
    "ru": "icons/mmoson-logo.png",
    "en": "icons/mmoson-logo-en.png",
}
LOGO_MAX_WIDTH = 512


def link(page: dict, active: str) -> tuple[str, str, str]:
    """Return a page URL, active class and accessible current-page marker."""
    is_active = page["slug"] == active
    css_class = ' class="active"' if is_active else ""
    current = ' aria-current="page"' if is_active else ""
    return page["output"], css_class, current


def nav_html(active: str) -> str:
    current_page = next(page for page in PAGES if page["slug"] == active)
    lang = current_page.get("lang", "ru")
    pages = [page for page in PAGES if page.get("lang", "ru") == lang]
    home = next(page for page in pages if page["slug"].startswith("index"))
    brand = "ММОСО’Н" if lang == "ru" else "MMOSO'N"
    nav_label = "Основная навигация" if lang == "ru" else "Primary navigation"
    menu_label = "Меню" if lang == "ru" else "Menu"

    items = []
    for page in pages:
        href, css_class, current = link(page, active)
        items.append(
            f'      <li><a href="{href}" data-page="{page["slug"]}"{css_class}{current}>'
            f'{page["nav"]}</a></li>'
        )
    mark = (
        f'<img class="nav-mark" data-site-logo="nav" data-logo-language="{lang}" '
        f'src="{LOGO_ASSETS[lang]}" alt="" aria-hidden="true">'
    )
    return (
        '<header class="nav-wrap">\n'
        f'  <nav class="nav" aria-label="{nav_label}">\n'
        f'    <a href="{home["output"]}" data-page="{home["slug"]}" class="nav-brand">\n'
        f'      {mark}\n'
        f'      <span>{brand}</span>\n'
        '    </a>\n'
        f'    <button class="nav-toggle" aria-expanded="false" aria-controls="nav-links" aria-label="{menu_label}">\n'
        '      <span></span><span></span><span></span>\n'
        '    </button>\n'
        '    <ul class="nav-links" id="nav-links">\n'
        + "\n".join(items)
        + "\n    </ul>\n  </nav>\n</header>"
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
        '  </div>\n'
        '</section>'
    )


def pager_html(slug: str) -> str:
    current_page = next(page for page in PAGES if page["slug"] == slug)
    lang = current_page.get("lang", "ru")
    pages = [page for page in PAGES if page.get("lang", "ru") == lang]
    idx = pages.index(current_page)
    prev_page = pages[idx - 1] if idx > 0 else None
    next_page = pages[idx + 1] if idx + 1 < len(pages) else None
    back_label, next_label = ("Назад", "Дальше") if lang == "ru" else ("Previous", "Next")

    left = (
        f'  <a class="pager-prev" href="{prev_page["output"]}" data-page="{prev_page["slug"]}">\n'
        f'    <span class="pager-label">{back_label}</span>\n'
        f'    <span class="pager-name">← {prev_page["nav"]}</span>\n  </a>'
        if prev_page else '  <span aria-hidden="true"></span>'
    )
    right = (
        f'  <a class="pager-next" href="{next_page["output"]}" data-page="{next_page["slug"]}">\n'
        f'    <span class="pager-label">{next_label}</span>\n'
        f'    <span class="pager-name">{next_page["nav"]} →</span>\n  </a>'
        if next_page else '  <span aria-hidden="true"></span>'
    )
    label = "Переход между страницами" if lang == "ru" else "Page navigation"
    return '<nav class="pager" aria-label="' + label + '">\n' + left + "\n" + right + "\n</nav>"


def lightbox_html(language: str) -> str:
    label = "Просмотр изображения в полном размере" if language == "ru" else "Full-size image viewer"
    close_label = "Закрыть изображение" if language == "ru" else "Close image"
    return (
        f'<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" '
        f'aria-hidden="true" aria-label="{label}">\n'
        f'  <button class="lightbox-close" type="button" aria-label="{close_label}">×</button>\n'
        '  <figure>\n'
        '    <img id="lightbox-img" alt="">\n'
        '    <figcaption id="lightbox-caption"></figcaption>\n'
        '  </figure>\n'
        '</div>'
    )


def encode_image(path: Path, max_width: int = 1200, quality: int = 80) -> tuple[str, int]:
    raw = path.read_bytes()
    # SVG не конвертируем через PIL — возвращаем как есть (base64)
    if path.suffix.lower() == ".svg":
        return f"data:image/svg+xml;base64,{base64.b64encode(raw).decode('ascii')}", len(raw)
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}", len(raw)

    img = Image.open(io.BytesIO(raw))
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    img = img.convert("RGBA" if has_alpha else "RGB")
    width, height = img.size
    if width > max_width:
        img = img.resize((max_width, round(height * max_width / width)), Image.LANCZOS)
    buf = io.BytesIO()
    if has_alpha:
        img.save(buf, "PNG", optimize=True)
    else:
        img.save(buf, "WEBP", quality=quality, method=6)
    packed = buf.getvalue()
    if len(packed) >= len(raw):
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}", len(raw)
    mime = "image/png" if has_alpha else "image/webp"
    return f"data:{mime};base64,{base64.b64encode(packed).decode('ascii')}", len(packed)


def build(page: dict, css: str, js: str) -> tuple[str, int]:
    fragment = (CONTENT / f'{page["slug"]}.html').read_text(encoding="utf-8").strip()
    shell = page.get("shell", True)

    if not shell:
        body = '<div class="container">\n' + fragment + "\n</div>"
        return finish(page, body, css, js)

    if page.get("wrap_content"):
        fragment = '<div class="container">\n' + fragment + "\n</div>"

    parts = [nav_html(page["slug"]), '<main class="page" id="top">']
    head_block = page_head_html(page)
    if head_block:
        parts.append(head_block)
    parts.append(fragment)
    parts.append("</main>")
    if page.get("pager", True):
        parts.append(pager_html(page["slug"]))
    if page["slug"] in {"gallery", "gallery-en"}:
        parts.append(lightbox_html(page["lang"]))
    body = "\n\n".join(parts)
    return finish(page, body, css, js)

def finish(page: dict, body: str, css: str, js: str) -> tuple[str, int]:
    lang = page.get("lang", "ru")
    shell = page.get("shell", True)
    html_lang = lang

    if lang == "ru":
        page_comment = f"ММОСО’Н · страница «{page['nav']}»."
        html_note = "Самодостаточный HTML-файл: разметка, стили, скрипт и иллюстрации встроены."
        mode_note = (
            "Контентная HTML-страница без общей шапки."
            if not shell else "Самодостаточная страница сайта ММОСО’Н."
        )
        footer = """<footer class="footer">
  <div class="footer-inner">
    <div class="footer-title">ММОСО’Н</div>
    <div class="footer-copy">
      <strong>© Бугаенко Роман Сергеевич, 2026</strong><br>
      Использование материалов, размещённых на этом сайте, возможно только при обязательном указании автора и ссылки на источник.
    </div>
  </div>
</footer>""" if shell else ""
    else:
        page_comment = f"MMOSO'N · {page['nav']} page."
        html_note = "One self-contained HTML file: markup, styles, script and illustrations inline."
        mode_note = (
            "Standalone content HTML page without the shared header."
            if not shell else "Self-contained MMOSO'N website page."
        )
        footer = """<footer class="footer">
  <div class="footer-inner">
    <div class="footer-title">MMOSO'N</div>
    <div class="footer-copy">
      <strong>© Roman Sergeevich Bugaenko, 2026</strong><br>
      Materials on this site may be used only with clear attribution to the author and a link to the source.
    </div>
  </div>
</footer>""" if shell else ""

    html = f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page["title"]}</title>
<meta name="description" content="{page["desc"]}">
<meta name="theme-color" content="#8f7ed6">
<!-- {page_comment} {html_note} {mode_note} -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Raleway:wght@300;400;500;600;700&display=swap">
<link rel="icon" type="image/png" sizes="256x256" href="icons/favicon.png">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<style>
{css}
</style>
<noscript><style>.fade-in{{opacity:1!important;transform:none!important}}</style></noscript>
</head>
<body>

{body}

{footer}

<script>
{js}
</script>
</body>
</html>
"""

    settings = page.get("img", {})
    inlined = 0
    for rel in sorted(set(re.findall(r"assets/(?:fig_ru|fig_en)/[A-Za-z0-9_\-.]+\.png", html))):
        uri, size = encode_image(
            ROOT / rel,
            max_width=settings.get("max_width", 1200),
            quality=settings.get("quality", 80),
        )
        inlined += size
        html = html.replace(rel, uri)

    # Иконки и фото из site/icons/ — тоже встраиваем как data-URI
    for rel in sorted(set(re.findall(r"icons/[A-Za-z0-9_\-.]+\.(?:png|jpg|jpeg|svg)", html))):
        uri, size = encode_image(
            ROOT / rel,
            max_width=LOGO_MAX_WIDTH if rel in LOGO_ASSETS.values() else settings.get("max_width", 1200),
            quality=settings.get("quality", 80),
        )
        inlined += size
        html = html.replace(rel, uri)

    return html, inlined


def main() -> int:
    default_css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    RU_DIR.mkdir(exist_ok=True)
    EN_DIR.mkdir(exist_ok=True)
    PUBLISH_RU_DIR.mkdir(exist_ok=True)
    PUBLISH_EN_DIR.mkdir(exist_ok=True)
    print(f"стили: {len(default_css)/1024:.0f} КБ · скрипт: {len(js)/1024:.0f} КБ\n")

    rows = []
    for page in PAGES:
        css_files = page.get("css", "css/styles.css")
        if isinstance(css_files, str):
            css_files = [css_files]
        css = "\n\n".join((ROOT / css_file).read_text(encoding="utf-8") for css_file in css_files)
        html, inlined = build(page, css, js)
        lang = page.get("lang", "ru")
        folder = RU_DIR if lang == "ru" else EN_DIR
        out = folder / page["output"]
        out.write_text(html, encoding="utf-8")
        publish_folder = PUBLISH_RU_DIR if lang == "ru" else PUBLISH_EN_DIR
        (publish_folder / page["output"]).write_text(html, encoding="utf-8")
        local_refs = [
            x
            for x in re.findall(r'(?:src|href)="(?!https://|data:|#|mailto:|tel:)([^"]+)"', html)
            if not x.endswith(".html")
        ]
        left = []
        for ref in local_refs:
            target = ROOT.parent / ref.lstrip("/") if ref.startswith("/") else out.parent / ref
            if not target.exists():
                left.append(ref)
        rows.append((str(out.relative_to(ROOT)), out.stat().st_size, inlined, left, len(html)))

    for name, size, inlined, left, chars in rows:
        note = f"  ⚠ локальные ссылки: {left}" if left else ""
        print(f"{name:<24} {size/1024:6.0f} КБ  иллюстраций {inlined/1024:5.0f} КБ  символов {chars:>7,}{note}".replace(",", " "))

    total = sum(r[1] for r in rows)
    print(f"\nвсего {len(rows)} страниц, {total/1024/1024:.2f} МБ")
    print("Собранные файлы синхронизированы в корневые ru/ и en/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())