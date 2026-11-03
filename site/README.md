# Сайт ММОСО’Н / MMOSO'N Website

## Русский

Визуальный язык сайта: лавандовый фон, белые «стеклянные» карточки, Montserrat + Raleway, градиентные подчёркивания и акценты фиолетовый / коралловый / бирюзовый.

### Страницы и навигация

Сборщик генерирует **14 актуальных страниц** — по семь на каждом языке:

| Язык | Меню |
|---|---|
| Русский | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы |
| English | Home, Engineering, Verification, Gallery, Edition, Contacts, Authors |

Полноформатные страницы получают видимое меню только своего языка и пейджер «назад / дальше» по тому же языку. Переключателя языка на страницах нет. Контактные страницы (`shell: false`) — отдельные embed-страницы: без общей навигационной шапки, пейджера и локальных `.html`-ссылок; для них меню предоставляет Google Sites. На полноформатных страницах меню остаётся видимым и без JavaScript; скрипт только улучшает его компактный мобильный режим. Страница «Авторы» указывает Молодёжное общественное движение «Межрегиональный картографический Я-кластер» (МХ «КРЯК») как партнёра проекта в технологическом аспекте.

### Один HTML на страницу

Каждая готовая страница — отдельный самодостаточный HTML-файл: собственные CSS, JS и нужные изображения встроены внутрь. Во время просмотра не требуются локальные CSS/JS-файлы или отдельная загрузка иллюстраций. В полноформатных страницах ссылки ведут на соответствующие страницы того же языка.

### Исходники и сборка

```
site/
├── build_pages.py              сборщик; обновляет site/ru, site/en и корневые ru/, en/
├── content/*.html              разметка страниц без оболочки
├── css/styles.css              общие стили полноформатных страниц
├── css/contacts.css            самостоятельный стиль страницы контактов
├── js/app.js                   поведение меню, счётчиков и галереи
├── assets/fig_ru/*.png         русские иллюстрации
├── assets/fig_en/*.png         английские иллюстрации
├── icons/                      изображения для страницы контактов
├── ru/*.html                   собранные русские страницы
└── en/*.html                   собранные английские страницы
```

Финальные версии иллюстраций находятся в `assets/fig_ru/` и `assets/fig_en/`; чистые листы без подписей в текущем наборе сайта не используются.

```bash
python3 site/build_pages.py
```

Сборка создаёт 14 страниц, встраивает стили, скрипт и изображения и синхронизирует результаты с корневыми `ru/` и `en/` для GitHub Pages. Файлы `ru/title.html` и `site/ru/title.html` — оставшиеся старые сборки, не входящие в текущий набор; скрипт их не создаёт и не удаляет до отдельного решения.

### Локальный просмотр

Из корня репозитория:

```bash
python3 -m http.server 8000
# http://localhost:8000/ru/index.html
# http://localhost:8000/en/index.html
```

---

## English

The visual style uses a lavender background, white glass-like cards, Montserrat + Raleway, gradient underlines, and violet / coral / turquoise accents.

### Pages and navigation

The builder generates **14 current pages**, seven per language:

| Language | Menu |
|---|---|
| Русский | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы |
| English | Home, Engineering, Verification, Gallery, Edition, Contacts, Authors |

Full website pages have a visible menu and previous/next pager limited to their own language. There is no language switcher. Contact pages (`shell: false`) are embed pages: no shared navigation header, pager or local `.html` links; Google Sites supplies their menu. On full pages, navigation remains visible without JavaScript; the script only enhances the compact mobile menu. The Authors page identifies the Youth Public Movement “Interregional Cartographic Ya-Cluster” (official Russian name: Молодёжное общественное движение «Межрегиональный картографический Я-кластер», abbreviated МХ «КРЯК») as a partner in the project’s technological aspect.

### One HTML file per page

Every built page is a self-contained HTML file with its CSS, JavaScript and required illustrations embedded. Local CSS/JS files and separately loaded images are not needed at runtime. Full-page links stay within the same language.

### Sources and build

```
site/
├── build_pages.py              builds site/ru, site/en and root ru/, en/
├── content/*.html              page markup without the wrapper
├── css/styles.css              shared full-page styles
├── css/contacts.css            standalone contact-page style
├── js/app.js                   menu, counters and gallery behavior
├── assets/fig_ru/*.png         Russian illustrations
├── assets/fig_en/*.png         English illustrations
├── icons/                      images for the contact page
├── ru/*.html                   built Russian pages
└── en/*.html                   built English pages
```

Final gallery illustrations are in `assets/fig_ru/` and `assets/fig_en/`; clean, text-free sheets are not used by the current website build.

```bash
python3 site/build_pages.py
```

The build creates 14 pages, inlines styles, scripts and images, then syncs the result to the root `ru/` and `en/` directories for GitHub Pages. `ru/title.html` and `site/ru/title.html` are retained legacy builds outside the current page set; the builder neither generates nor deletes them pending a separate decision.

### Local preview

From the repository root:

```bash
python3 -m http.server 8000
# http://localhost:8000/ru/index.html
# http://localhost:8000/en/index.html
```
