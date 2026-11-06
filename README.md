# ММОСО’Н / MMOSO'N

## Русская версия

**Модуль моделирования орбитальной станции О’Нилла** — личный инженерный и научно-исследовательский проект Бугаенко Романа Сергеевича. Это расчётная модель обитаемой двухцилиндровой станции в окрестности точки L1 Земля—Солнце, а не утверждённый проект строительства.

### Техническая документация

Текущая публикация — **редакция 8 от 6 ноября 2026 года**. Она содержит по одному объединённому DOCX на каждый язык: 43 компонента, включая 34 нумерованных технических раздела (1–34), вводные материалы, приложения и лицензию. Маркировка проверяется по самим DOCX, а не по этому README.

| Файл | Что содержит | Проверка |
|---|---|---|
| `sections/MMOSON_combined_document_ru.docx` | Русская версия технической документации, разделы 1–34 | Редакция 8; 72 таблицы; 24 встроенных рисунка |
| `sections/MMOSON_combined_document_en.docx` | Английская версия технической документации, разделы 1–34 | Edition 8; 70 таблиц; 24 встроенных рисунка |

Оба файла имеют титульные страницы с отдельными строками автора и места/года, 42 датированные отметки компонентов и разделы 1–34. В русской версии вне единого общего списка литературы используются русские формулировки; названия источников в общей библиографии сохраняют оригинальное написание. Списки литературы по разделам удалены, а примечания матрицы статусов сохранены. Имена существующих файлов и URL репозитория сохранены для совместимости; в содержимом публикации и интерфейсе используется написание MMOSO'N.

### Основные параметры модели

| Величина | Значение |
|---|---|
| Радиус цилиндра | 5 000 м |
| Длина цилиндрической части | 40 км (полная длина — 49 км) |
| Число цилиндров | 2, встречного вращения |
| Угловая скорость | 0,04429 рад/с (0,423 об/мин) |
| Тяжесть на ободе | 1,0 g |
| Материал силового пояса | сталь 18Ni(300), толщина 850 мм |
| Площадь | 3 100,2 км² суммарно; 1 550,1 км² на цилиндр |
| Масса станции | 46,70 млрд т |
| Население | 1 000 000 человек |
| Электрическая мощность | 721,4 ГВт |
| Размещение | окрестность точки L1 Земля—Солнце |

Внутреннее освещение и светотепловой баланс обеспечиваются осевыми реакторными балками. Модель не предусматривает зеркала, ориентированные на Солнце, или солнечный парус.

### Проверки и расчёты

Установите зависимости из `requirements.txt`, затем из корня репозитория выполните:

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q src tools site
python3 site/build_pages.py
python3 site/check_site_build.py
python3 src/check_edition8_docs.py
python3 src/crosscheck.py sections
python3 src/audit_tables_figures_v7.py sections
python3 src/check_transport_interface.py
python3 src/edition8_calcs.py
```

`check_edition8_docs.py` сверяет титульные страницы и оформление по ГОСТ 7.32–2017 (A4, поля 3 / 1,5 / 2 / 2 см, Times New Roman 14 pt для основного текста, интервал 1,5, отступ первой строки 1,25 см, Times New Roman 12 pt для таблиц), языковую локализацию вне общей библиографии, единый список из 31 источника, 15 примечаний матрицы статусов, маркировку редакции 8 от 6 ноября 2026 г., 42 отметки компонентов, разделы 1–34 и точное число таблиц: 72 в русском и 70 в английском DOCX. Сквозная сверка проверяет канонические значения и эти числа для опубликованных документов; `audit_tables_figures_v7.py` дополнительно сверяет таблицы, подписи, целостность PNG и полный комплект из 24 локализованных рисунков в каждом языке. Чистые исходники `src/fig/` в текущем репозитории не хранятся.

`check_transport_interface.py` проверяет канал размером 20,80 м при проёме 30,00 м, маршрут 7 430,8 м и расчётную пропускную способность. `edition8_calcs.py` пересчитывает семь областей редакции 8 (A–G) и сохраняет результат в `src/edition8_results.json`.

**Результаты редакции 8, влияющие на модель:**

- генетика: не менее 5 000 основателей и 200 несвязанных семейных линий; обмен родителями между цилиндрами — не менее 1 % за поколение; банк гамет — от 10 000 доноров;
- сельское хозяйство: таблица 5.2 раздельно показывает годовую потребность, сценарный инвентарь и валовой/нетто-выпуск; совокупные потери 20 % — модельное допущение. ×1,83 и ×2,73 — отношения годового нетто-выпуска к годовой потребности, а не складские запасы. Таблица 5.4 содержит 2,216 трлн ккал валового выпуска культур против 2,338 трлн ккал валового итога системы; остаток 0,122 трлн ккал и белковая невязка 2 020 т требуют сверки по животноводству и аквакультуре. Предварительный сценарий ×1,15 по калориям и ×1,20 по белку даёт 462,7 км² посевов и условное высвобождение 344,3 км², но белковый выпуск в минимальном решении остаётся около ×2,49 потребности, а точное снижение до ×1,20 не достигается. Это не утверждённый план выпуска или землепользования; холодная зона остаётся ресурсом для проверки многоярусного выращивания;
- промышленность: при 5 % открытого металла коррозионный поток составляет 12,17 млн т стали и связывает 5,23 млн т кислорода в год; покрытия снижают оценку скорости коррозии в десять раз;
- стыковка: при заданном карантине лимитирует необходимая вместимость карантинного контура;
- экосистема: расчётные популяции кошек — 6 000; для тепличного опыления отдельно учитываются 320 000 семей шмелей;
- города: рассматриваются двадцать городов по 50 000 человек и виртуальный двойник в масштабе 1:100.

Это результаты расчётной модели, а не сертификация станции или доказательство технологической готовности.

### Сборка публикации

`tools/combine_sections.py` собирает языковые DOCX из **43 исходных двуязычных DOCX-компонентов**, сохраняя таблицы и текст, затем встраивает все 24 иллюстрации из соответствующего набора `site/assets/fig_ru/` или `site/assets/fig_en/`:

```bash
python3 tools/combine_sections.py --src /path/to/43-component-docx --out-dir sections --language both
```

Исходные компоненты не входят в текущий рабочий каталог; в `sections/` хранятся готовые объединённые документы. Для пересборки нужны сами исходные DOCX. Скрипт не считает уже объединённые файлы исходными компонентами и откажется собирать их повторно как вход.

### Подготовка и форматирование итоговых DOCX

`tools/prepare_edition8_documents.py` оформляет раздельные строки титульного листа, приводит русские вводные материалы к одному языку, удаляет дублирующиеся списки литературы по разделам и сохраняет единую библиографию из 31 позиции и примечания матрицы статусов. Также текст иллюстраций приводится к комплекту из 24 рисунков редакции 8.

`tools/format_docs_like_reference.py` применяет к обеим версиям редакции 8 оформление научно-технического отчёта по ГОСТ 7.32–2017: титул с автором и городом/годом, A4, поля 3 / 1,5 / 2 / 2 см, Times New Roman 14 pt для основного текста, интервал 1,5, отступ первой строки 1,25 см и 12 pt для таблиц; заголовки повторяются на новых страницах, строки таблиц не разрываются.

```bash
python3 tools/prepare_edition8_documents.py
python3 tools/format_docs_like_reference.py
```

### Сайт

Исходники сайта находятся в `site/`. Каждая опубликованная страница — самодостаточный HTML-файл со встроенными стилями, скриптом и нужными изображениями. Сборщик создаёт 14 страниц (7 русских и 7 английских) в `site/ru/`, `site/en/` и синхронизирует их с корневыми `ru/`, `en/`:

```bash
python3 site/build_pages.py
```

На русской и английской главных страницах показаны оригинальные логотипы соответствующих языковых версий вместо видимых текстовых названий; доступные для экранных дикторов заголовки сохранены в разметке. Английский логотип с прозрачным фоном встроен также в навигацию всех английских страниц. На главной странице есть кнопка перехода к версии на другом языке; меню и пейджеры полноформатных страниц остаются внутри своего языка. На страницах «Контакты» есть пейджер «Назад / Дальше» между «Изданием» и «Авторами», общая навигационная шапка и локализованный подвал. Обе галереи содержат все 24 листа; страница «Издание» отражает редакцию 8 и ведёт к одному объединённому DOCX на язык. Меню доступно и без JavaScript. `site/check_site_build.py` проверяет состав 14 страниц, синхронизацию опубликованных копий и правильное встраивание языкового логотипа в навигацию и на обе главные страницы.

`ru/title.html` и `site/ru/title.html` — старые файлы сборки, не входящие в текущий набор 14 страниц. Они не пересобираются и не удаляются; написание названия проекта в них также приведено к актуальному варианту.

### Состав репозитория

- `sections/` — две итоговые объединённые DOCX-версии редакции 8.
- `favicon.ico` — многоразмерный фавикон, созданный из предоставленной эмблемы; PNG-версия встроена в страницы.
- `site/icons/mmoson-logo.png` и `site/icons/mmoson-logo-en.png` — оригинальные логотипы для русской и английской версий; английский PNG сохраняет прозрачный фон и используется на английских страницах.
- `src/` — расчёты и проверки документации.
- `tools/` — утилиты сборки, работы с иллюстрациями и локальные вспомогательные инструменты.
- `site/content/`, `site/css/`, `site/js/` — исходники страниц и оформления.
- `site/assets/fig_ru/`, `site/assets/fig_en/` — финальные русские и английские иллюстрации галереи.
- `ru/`, `en/` — опубликованные HTML-страницы для GitHub Pages.
- `MMOSON_supplement_new_domains.docx` — архивный документ по разделам 20–27; актуальный текст этих разделов также входит в объединённые документы редакции 8.

### Автор и статус

**Бугаенко Роман Сергеевич** — автор личного проекта ММОСО’Н. Молодёжное общественное движение «Межрегиональный картографический Я-кластер» (МХ «КРЯК») — технологический партнёр проекта и может предоставить устройства, использующие микроконтроллеры ESP32. Публикация является концептуальным исследованием, а не рабочей конструкторской документацией и не готовым к полёту проектом.

Материалы распространяются по условию **«Все права защищены / All rights reserved»**. Публичное чтение разрешено; иное использование требует предварительного письменного согласия автора.

---

## English version

**MMOSO'N — Modeling Module for an O’Neill Orbital Station** is Roman Sergeevich Bugaenko’s personal engineering and research project. It is a calculation model of a habitable two-cylinder station near the Earth–Sun L1 point, not an approved construction design.

### Technical documentation

The current publication is **Edition 8, dated 6 November 2026**. It contains one combined DOCX per language, with 43 components, including 34 numbered technical sections (1–34), front matter, appendices and the licence. The edition is verified in the DOCX files themselves, not inferred from this README.

| File | Contents | Verified structure |
|---|---|---|
| `sections/MMOSON_combined_document_ru.docx` | Russian technical-documentation edition, sections 1–34 | Edition 8; 72 tables; 24 embedded figures |
| `sections/MMOSON_combined_document_en.docx` | English technical-documentation edition, sections 1–34 | Edition 8; 70 tables; 24 embedded figures |

Both files have title pages with separate project-lead and place/year lines, 42 dated component stamps and sections 1–34. The Russian version uses Russian wording outside its single shared bibliography; source titles in that list retain their original spelling. Section-level reference lists have been removed, while the status-matrix notes remain. Existing file names and repository URLs are retained for compatibility; the displayed project name in the publication and website uses the spelling MMOSO'N.

### Model parameters

| Parameter | Value |
|---|---|
| Cylinder radius | 5,000 m |
| Cylindrical section length | 40 km (49 km overall) |
| Number of cylinders | 2, counter-rotating |
| Angular velocity | 0.04429 rad/s (0.423 rpm) |
| Rim gravity | 1.0 g |
| Load-bearing belt | 18Ni(300) steel, 850 mm thick |
| Area | 3,100.2 km² total; 1,550.1 km² per cylinder |
| Station mass | 46.70 billion tonnes |
| Population | 1,000,000 people |
| Electrical power | 721.4 GW |
| Location | Near the Earth–Sun L1 point |

Interior lighting and the light/thermal balance are provided by axial reactor-powered beams. The model does not use Sun-facing mirrors or a solar sail.

### Checks and calculations

Install the dependencies from `requirements.txt`, then run from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q src tools site
python3 site/build_pages.py
python3 site/check_site_build.py
python3 src/check_edition8_docs.py
python3 src/crosscheck.py sections
python3 src/audit_tables_figures_v7.py sections
python3 src/check_transport_interface.py
python3 src/edition8_calcs.py
```

`check_edition8_docs.py` verifies both title pages and the GOST 7.32–2017-oriented layout (A4, 3 / 1.5 / 2 / 2 cm margins, Times New Roman 14 pt body text, 1.5 line spacing, a 1.25 cm first-line indent and Times New Roman 12 pt tables), localization outside the shared bibliography, the single list of 31 sources, 15 status-matrix notes, Edition 8 labels dated 6 November 2026, 42 component stamps, sections 1–34 and the exact table counts: 72 in the Russian DOCX and 70 in the English DOCX. The publication cross-check verifies canonical values and these counts for the published files; `audit_tables_figures_v7.py` additionally checks tables, captions, PNG integrity and the complete set of 24 localized figures in each language. Clean source images in `src/fig/` are not stored in the current repository.

`check_transport_interface.py` checks the 20.80 m channel against a 30.00 m opening, the 7,430.8 m route and calculated throughput. `edition8_calcs.py` recalculates the seven Edition 8 domains (A–G) and writes `src/edition8_results.json`.

**Edition 8 results that affect the model:**

- genetics: at least 5,000 founders and 200 unrelated family lines; parent exchange between cylinders of at least 1 % per generation; a gamete bank with at least 10,000 donors;
- agriculture: Table 5.2 separates annual need, scenario inventory and gross/net output; the aggregate 20% loss is a modelling assumption. ×1.83 and ×2.73 are annual net-output-to-annual-need ratios, not stock sizes. Table 5.4 reports 2.216 trillion kcal of gross crop output versus 2.338 trillion kcal of whole-system gross output; the 0.122-trillion-kcal residual and a 2,020-ton protein discrepancy require reconciliation against livestock and aquaculture. The preliminary ×1.15-calorie/×1.20-protein scenario gives 462.7 km² of cropland and a conditional 344.3 km² release, but protein output in the minimum-area solution remains about ×2.49 of need and cannot be reduced exactly to ×1.20 under current constraints. This is not an approved production or land-use plan; the cold zone remains a resource for evaluating multilayer cultivation;
- industry: with 5 % exposed metal, the corrosion stream is estimated at 12.17 million tonnes of steel and 5.23 million tonnes of oxygen per year; coatings reduce the corrosion-rate estimate tenfold;
- docking: under the stated quarantine model, required quarantine capacity is the limiting factor;
- ecosystem: the model uses 6,000 cats and separately accounts for 320,000 bumblebee colonies for greenhouse pollination;
- cities: twenty cities of 50,000 people are considered, together with a 1:100 virtual twin.

These are model calculations, not station certification or proof of technological readiness.

### Building the publication

`tools/combine_sections.py` assembles language-specific DOCX files from **43 bilingual source DOCX components**, preserving tables and text, then embeds all 24 figures from the matching `site/assets/fig_ru/` or `site/assets/fig_en/` set:

```bash
python3 tools/combine_sections.py --src /path/to/43-component-docx --out-dir sections --language both
```

The source components are not in the current working tree; `sections/` contains the final combined documents. Rebuilding requires the source DOCX files. The script rejects the combined outputs as component input.

### Preparing and formatting the final DOCX files

`tools/prepare_edition8_documents.py` creates separate cover lines, localizes the Russian front matter, removes duplicated section-level reference lists, and keeps the single 31-item bibliography and the status-matrix notes. It also updates illustration notes to the 24-sheet Edition 8 set.

`tools/format_docs_like_reference.py` applies a GOST 7.32–2017-oriented scientific-report layout to both Edition 8 files: title page with project lead and place/year, A4, left / right / top / bottom margins of 3 / 1.5 / 2 / 2 cm, Times New Roman 14 pt body text, 1.5 line spacing, a 1.25 cm first-line indent and 12 pt table text; table headers repeat across pages and rows do not split.

```bash
python3 tools/prepare_edition8_documents.py
python3 tools/format_docs_like_reference.py
```

### Website

Website sources are in `site/`. Each published page is a self-contained HTML file with its CSS, script and required illustrations embedded. The builder creates 14 pages (7 Russian and 7 English) in `site/ru/` and `site/en/`, then syncs them to the root `ru/` and `en/` directories:

```bash
python3 site/build_pages.py
```

The Russian and English home pages display the original language-specific project logos in place of visible text titles; accessible headings remain in the markup. The transparent English logo is also embedded in the navigation on all English pages. Home pages include a button to switch between Russian and English. Full-page menus and pagers stay within the current language. Contact pages include the shared navigation header and localized footer; the English Previous/Next pager links Edition and Authors, while the Russian «Назад / Дальше» pager links «Издание» and «Авторы». Both galleries contain all 24 sheets; the Edition page reflects Edition 8 and links to one combined DOCX per language. Navigation remains visible without JavaScript. `site/check_site_build.py` verifies the 14-page set, synchronization of published copies, and correct embedding of the language-specific logo in navigation and both home pages.

`ru/title.html` and `site/ru/title.html` are legacy build files outside the current 14-page set. They are not rebuilt or deleted; their displayed project name has also been updated to the current spelling.

### Repository contents

- `sections/` — the two final combined Edition 8 DOCX files.
- `favicon.ico` — multi-resolution site favicon derived from the supplied emblem; the PNG rendition is inlined in pages.
- `site/icons/mmoson-logo.png` and `site/icons/mmoson-logo-en.png` — original Russian and English project logos; the transparent English PNG is used on English pages.
- `src/` — calculations and documentation checks.
- `tools/` — document, image and local utility scripts.
- `site/content/`, `site/css/`, `site/js/` — page sources and styling.
- `site/assets/fig_ru/`, `site/assets/fig_en/` — final Russian and English gallery illustrations.
- `ru/`, `en/` — published HTML pages for GitHub Pages.
- `MMOSON_supplement_new_domains.docx` — archived document for sections 20–27; their current text is also included in the combined Edition 8 files.

### Author and status

**Roman Sergeevich Bugaenko** is the author of the personal MMOSO'N project. The Youth Public Movement «Interregional Cartographic Ya-Cluster» is the project’s technological partner and may provide devices using ESP32 microcontrollers. This is a conceptual research publication, not working design documentation or a flight-ready project.

The materials are provided under an **“All rights reserved / Все права защищены”** notice. Public reading is permitted; other uses require the author’s prior written consent.
