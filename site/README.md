# Сайт ММОСО’Н / MMOSON Website

## Русский / Russian

Визуальный язык — по референсу МХ «КРЯК»: лавандовый фон, белые «стеклянные» секции-карточки, Montserrat + Raleway, градиентные подчёркивания, акценты фиолетовый / коралловый / бирюзовый.

### Главное

Каждая страница — **один самодостаточный HTML-файл**: разметка, весь CSS, весь JS и её собственные иллюстрации (`data:image/webp`) внутри. Отдельных `css/`, `js/` и папки с картинками во время работы страницы не требуется.

Страницы распределены по языковым папкам:

| Папка | Язык | Страницы |
|---|---|---|
| `site/ru/` | Русский | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы и лицензия, Титульная |
| `site/en/` | Английский | Main, Engineering, Verification, Gallery, Edition, Contacts, Authors and License |

В `ru/` и `en/` нет ссылок на другие `.html`-файлы (все страницы самодостаточные):

```bash
grep -o 'href="[^"]*\.html"' site/ru/*.html site/en/*.html    # вывод пустой
```

### Исходники и пересборка

```
site/
├── build_pages.py              сборка всех страниц
├── content/*.html              разметка страниц без обвязки — правится здесь
├── content/_parts/*.html       исходные фрагменты
├── css/styles.css              общий стиль (вшивается в каждую страницу)
├── css/contacts.css            своя таблица стилей страницы «Контакты»
├── js/app.js                   общее поведение (вшивается в каждую страницу)
├── assets/fig/*.png            иллюстрации в исходном разрешении
├── icons/*.png                 иконки и фото (вшиваются как data-URI)
├── IMAGE-MANIFEST.md           список иллюстраций публикации
├── README.md                   этот файл
├── ru/*.html                   готовые русские страницы
└── en/*.html                   готовые английские страницы
```

```bash
python3 site/build_pages.py
```

Сборка вшивает CSS и JS в каждую страницу, перекодирует нужные ей иллюстрации в WebP/PNG и печатает размеры. Правки текста — в `content/`, правки оформления — в `css/styles.css`, после этого достаточно повторить сборку.

### Локальный просмотр

```bash
cd site
python3 -m http.server 8000     # http://localhost:8000
# Затем откройте http://localhost:8000/ru/title.html или http://localhost:8000/en/index.html
```

## English / English

Visual language — by reference of MX «КРЯК»: lavender background, white «glass» card-sections, Montserrat + Raleway, gradient underlines, accents violet / coral / turquoise.

### Main

Each page is **one self-contained HTML file**: markup, all CSS, all JS, and its own illustrations (`data:image/webp`) inside. No separate `css/`, `js/`, or image folders are needed at runtime.

Pages are distributed into language folders:

| Folder | Language | Pages |
|---|---|---|
| `site/ru/` | Russian | Главная, Инженерия, Верификация, Иллюстрации, Издание, Контакты, Авторы и лицензия, Титульная |
| `site/en/` | English | Main, Engineering, Verification, Gallery, Edition, Contacts, Authors and License |

There are no links to other `.html` files in `ru/` or `en/` (all pages are self-contained):

```bash
grep -o 'href="[^"]*\.html"' site/ru/*.html site/en/*.html    # output empty
```

### Sources and rebuild

```
site/
├── build_pages.py              builds all pages
├── content/*.html              page markup without wrapper — edit here
├── content/_parts/*.html       source fragments
├── css/styles.css              common style (inlined into each page)
├── css/contacts.css            dedicated style for the «Contacts» page
├── js/app.js                   common behavior (inlined into each page)
├── assets/fig/*.png            illustrations in original resolution
├── icons/*.png                 icons and photos (inlined as data-URI)
├── IMAGE-MANIFEST.md           list of publication illustrations
├── README.md                   this file
├── ru/*.html                   ready Russian pages
└── en/*.html                   ready English pages
```

```bash
python3 site/build_pages.py
```

The build inlines CSS and JS into each page, re-encodes required illustrations to WebP/PNG, and prints sizes. Edit text in `content/`, edit styling in `css/styles.css`, then rerun the build.

### Local preview

```bash
cd site
python3 -m http.server 8000     # http://localhost:8000
# Then open http://localhost:8000/ru/title.html or http://localhost:8000/en/index.html
```
