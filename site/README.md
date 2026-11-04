# Сайт ММОСО’Н / MMOSO'N Website

## Русский

Визуальный язык сайта: лавандовый фон, белые «стеклянные» карточки, Montserrat + Raleway, градиентные подчёркивания и акценты фиолетовый / коралловый / бирюзовый.

### Страницы и навигация

Сборщик генерирует **14 актуальных страниц** — по семь на каждом языке:

| Язык | Меню |
|---|---|
| Русский | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы |
| English | Home, Engineering, Verification, Gallery, Edition, Contacts, Authors |

Главные страницы включают кнопку перехода между русской и английской версиями. Полноформатные страницы получают меню только своего языка и пейджер; страницы «Контакты» дополнительно связывают пейджером «Назад / Дальше» страницы «Издание» и «Авторы». Обе галереи содержат все 24 листа на соответствующем языке: русская — 24 русские иллюстрации, английская — 24 английские. Страница «Издание» указывает редакцию 8 и предлагает по одному объединённому DOCX на язык. Меню доступно без JavaScript; скрипт только улучшает его мобильный режим. На странице «Авторы» Молодёжное общественное движение «Межрегиональный картографический Я-кластер» (МХ «КРЯК») указано только как технологический партнёр проекта, который может предоставить устройства с микроконтроллерами ESP32.

### Один HTML на страницу

Каждая готовая страница — отдельный самодостаточный HTML-файл: собственные CSS, JS и нужные изображения встроены внутрь. Во время просмотра не требуются локальные CSS/JS-файлы или отдельная загрузка иллюстраций. В полноформатных страницах ссылки ведут на соответствующие страницы того же языка.

### Исходники и сборка

```
site/
├── build_pages.py              сборщик; обновляет site/ru, site/en и корневые ru/, en/
├── content/*.html              разметка страниц без оболочки
├── css/styles.css              общие стили полноформатных страниц
├── css/contacts.css            дополнительные стили страницы контактов
├── js/app.js                   поведение меню, счётчиков и галереи
├── assets/fig_ru/*.png         русские иллюстрации
├── assets/fig_en/*.png         английские иллюстрации
├── icons/                      изображения контактов, авторов и встроенный PNG-фавикон
├── ru/*.html                   собранные русские страницы
└── en/*.html                   собранные английские страницы
```

Финальные локализованные иллюстрации находятся в `assets/fig_ru/` и `assets/fig_en/`; чистые листы без подписей в текущем наборе сайта не используются. Обе галереи показывают все 24 листа на своём языке. Значок сайта собран из предоставленной эмблемы: `site/icons/favicon.png` встроен в страницы, многоразмерный `favicon.ico` лежит в корне публикации.

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

Home pages include a button to switch between Russian and English. Full pages have a language-specific menu and pager. Contact pages also include localized pagers: the English Previous/Next links Edition and Authors, while the Russian «Назад / Дальше» links «Издание» and «Авторы». Both galleries contain all 24 sheets in their respective languages: the Russian gallery uses 24 Russian illustrations, and the English gallery uses 24 English illustrations. The Edition page identifies Edition 8 and links to one combined DOCX per language. Navigation remains visible without JavaScript; the script only enhances the compact mobile menu. The Authors page identifies the Youth Public Movement «Interregional Cartographic Ya-Cluster» only as the project’s technological partner, which may provide devices using ESP32 microcontrollers.

### One HTML file per page

Every built page is a self-contained HTML file with its CSS, JavaScript and required illustrations embedded. Local CSS/JS files and separately loaded images are not needed at runtime. Full-page links stay within the same language.

### Sources and build

```
site/
├── build_pages.py              builds site/ru, site/en and root ru/, en/
├── content/*.html              page markup without the wrapper
├── css/styles.css              shared full-page styles
├── css/contacts.css            contact-page-specific styles
├── js/app.js                   menu, counters and gallery behavior
├── assets/fig_ru/*.png         Russian illustrations
├── assets/fig_en/*.png         English illustrations
├── icons/                      contact/author images and embedded PNG favicon
├── ru/*.html                   built Russian pages
└── en/*.html                   built English pages
```

Final localized illustrations are in `assets/fig_ru/` and `assets/fig_en/`; clean, text-free sheets are not used by the current website build. Both galleries show all 24 sheets in their respective language. The logo-derived `site/icons/favicon.png` is inlined into pages; the multi-resolution `favicon.ico` is at the publication root.

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
