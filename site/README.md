# Сайт ММОСО’Н / MMOSO'N Website

## Русский

Визуальный язык сайта: лавандовый фон, белые «стеклянные» карточки, Montserrat + Raleway, градиентные подчёркивания и акценты фиолетовый / коралловый / бирюзовый.

### Страницы и навигация

Сборщик генерирует **14 актуальных страниц** — по семь на каждом языке:

| Язык | Меню |
|---|---|
| Русский | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы |
| English | Home, Engineering, Verification, Gallery, Edition, Contacts, Authors |

Главные страницы включают кнопку перехода между русской и английской версиями. Полноформатные страницы получают меню только своего языка и пейджер «назад / дальше»; контактные страницы также имеют общее меню и локализованный подвал, но без пейджера. Меню доступно без JavaScript; скрипт только улучшает его мобильный режим. На странице «Авторы» Молодёжное общественное движение «Межрегиональный картографический Я-кластер» (МХ «КРЯК») указано как партнёр проекта в технологическом аспекте.

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
├── icons/                      изображения страниц контактов и авторов
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

Home pages include a button to switch between Russian and English. Full pages have a language-specific menu and previous/next pager. Contact pages include the shared navigation and localized footer, but no pager. Navigation remains visible without JavaScript; the script only enhances the compact mobile menu. The Authors page identifies the Youth Public Movement “Interregional Cartographic Ya-Cluster” (official Russian name: Молодёжное общественное движение «Межрегиональный картографический Я-кластер», abbreviated МХ «КРЯК») as a partner in the project’s technological aspect.

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
├── icons/                      images for contact and authors pages
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
