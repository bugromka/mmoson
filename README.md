# ММОСО’Н / MMOSO'N

## Русская версия

**Модуль моделирования орбитальной станции О’Нилла** — личный инженерный и научно-исследовательский проект Бугаенко Романа Сергеевича. Это расчётная модель обитаемой двухцилиндровой станции в окрестности точки L1 Земля—Солнце, а не утверждённый проект строительства.

### Техническая документация

Текущая публикация — **редакция 8 от 31 октября 2026 года**. В ней 43 компонента, включая 34 нумерованных технических раздела (1–34), вводные материалы, приложения и лицензию. Маркировка проверяется по самому DOCX, а не по этому README.

| Файл | Что содержит | Проверка |
|---|---|---|
| `sections/MMOSON_combined_document_ru.docx` | Русская версия технической документации, разделы 1–34 | Редакция 8; 69 таблиц; 23 встроенных рисунка |
| `sections/MMOSON_combined_document_en.docx` | Английская версия технической документации, разделы 1–34 | Edition 8; 67 таблиц; 23 встроенных рисунка |

В обоих файлах есть титульная маркировка редакции 8, 42 датированных отметки компонентов и разделы 1–34. Страница содержания русской версии сохраняет исходные двуязычные обозначения; основное содержание собрано по соответствующему языку. Имена существующих файлов и URL репозитория сохранены для совместимости; в содержимом публикации и интерфейсе используется написание MMOSO'N.

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
python3 src/check_edition8_docs.py
python3 src/crosscheck.py sections
python3 src/audit_tables_figures_v7.py sections
python3 src/check_transport_interface.py
python3 src/edition8_calcs.py
```

`check_edition8_docs.py` сверяет видимую маркировку и написание названия проекта в обоих DOCX, 42 отметки компонентов, разделы 1–34, таблицы, подписи и встроенные рисунки. Сквозная сверка и аудит публикации проходят на текущих объединённых документах. Аудит также проверяет целостность PNG внутри DOCX; отдельные исходники `src/fig/` в текущем репозитории не хранятся, поэтому сравнение с ними пропускается с предупреждением.

`check_transport_interface.py` проверяет канал размером 20,80 м при проёме 30,00 м, маршрут 7 430,8 м и расчётную пропускную способность. `edition8_calcs.py` пересчитывает семь областей редакции 8 (A–G) и сохраняет результат в `src/edition8_results.json`.

**Результаты редакции 8, влияющие на модель:**

- генетика: не менее 5 000 основателей и 200 несвязанных семейных линий; обмен родителями между цилиндрами — не менее 1 % за поколение; банк гамет — от 10 000 доноров;
- сельское хозяйство: выявлена несостыковка 15,6 % между валовой и нетто-продукцией; требуется уточнить потери или исходную таблицу. Снижение белкового резерва к ×1,20 освобождает расчётные 395 км²; холодная зона остаётся крупным резервом многоярусного выращивания;
- промышленность: при 5 % открытого металла коррозионный поток составляет 12,17 млн т стали и связывает 5,23 млн т кислорода в год; покрытия снижают оценку скорости коррозии в десять раз;
- стыковка: при заданном карантине лимитирует необходимая вместимость карантинного контура;
- экосистема: расчётные популяции кошек — 6 000; для тепличного опыления отдельно учитываются 320 000 семей шмелей;
- города: рассматриваются двадцать городов по 50 000 человек и виртуальный двойник в масштабе 1:100.

Это результаты расчётной модели, а не сертификация станции или доказательство технологической готовности.

### Сборка публикации

`tools/combine_sections.py` собирает языковые DOCX из **43 исходных двуязычных DOCX-компонентов**, сохраняя таблицы и изображения:

```bash
python3 tools/combine_sections.py --src /path/to/43-component-docx --out-dir sections --language both
```

Исходные компоненты не входят в текущий рабочий каталог; в `sections/` хранятся готовые объединённые документы. Для пересборки нужны сами исходные DOCX. Скрипт не считает уже объединённые файлы исходными компонентами и откажется собирать их повторно как вход.

### Сайт

Исходники сайта находятся в `site/`. Каждая опубликованная страница — самодостаточный HTML-файл со встроенными стилями, скриптом и нужными изображениями. Сборщик создаёт 14 страниц (7 русских и 7 английских) в `site/ru/`, `site/en/` и синхронизирует их с корневыми `ru/`, `en/`:

```bash
python3 site/build_pages.py
```

На главной странице есть кнопка перехода к версии на другом языке; меню и пейджеры полноформатных страниц остаются внутри своего языка. Страницы контактов включают общую навигационную шапку и локализованный подвал, но не пейджер. Меню доступно и без JavaScript.

`ru/title.html` и `site/ru/title.html` — старые файлы сборки, не входящие в текущий набор 14 страниц. Они не пересобираются и не удаляются; написание названия проекта в них также приведено к актуальному варианту.

### Состав репозитория

- `sections/` — две итоговые объединённые DOCX-версии редакции 8.
- `src/` — расчёты и проверки документации.
- `tools/` — утилиты сборки, работы с иллюстрациями и локальные вспомогательные инструменты.
- `site/content/`, `site/css/`, `site/js/` — исходники страниц и оформления.
- `site/assets/fig_ru/`, `site/assets/fig_en/` — финальные русские и английские иллюстрации галереи.
- `ru/`, `en/` — опубликованные HTML-страницы для GitHub Pages.
- `MMOSON_supplement_new_domains.docx` — архивный документ по разделам 20–27; актуальный текст этих разделов также входит в объединённые документы редакции 8.

### Автор и статус

**Бугаенко Роман Сергеевич** — автор личного проекта ММОСО’Н. В технологическом аспекте партнёром проекта является Молодёжное общественное движение «Межрегиональный картографический Я-кластер» (сокр. МХ «КРЯК»). Публикация является концептуальным исследованием, а не рабочей конструкторской документацией и не готовым к полёту проектом.

Материалы распространяются по условию **«Все права защищены / All rights reserved»**. Публичное чтение разрешено; иное использование требует предварительного письменного согласия автора.

---

## English version

**MMOSO'N — Modeling Module for an O’Neill Orbital Station** is Roman Sergeevich Bugaenko’s personal engineering and research project. It is a calculation model of a habitable two-cylinder station near the Earth–Sun L1 point, not an approved construction design.

### Technical documentation

The current publication is **Edition 8, dated 31 October 2026**. It contains 43 components, including 34 numbered technical sections (1–34), front matter, appendices and the licence. The edition is verified in the DOCX files themselves, not inferred from this README.

| File | Contents | Verified structure |
|---|---|---|
| `sections/MMOSON_combined_document_ru.docx` | Russian technical-documentation edition, sections 1–34 | Edition 8; 69 tables; 23 embedded figures |
| `sections/MMOSON_combined_document_en.docx` | English technical-documentation edition, sections 1–34 | Edition 8; 67 tables; 23 embedded figures |

Both files have a visible Edition 8 title, 42 dated component stamps and sections 1–34. The Russian contents page retains its original bilingual labels; the main technical text is assembled by language. Existing file names and repository URLs are retained for compatibility; the displayed project name in the publication and website uses the spelling MMOSO'N.

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
python3 src/check_edition8_docs.py
python3 src/crosscheck.py sections
python3 src/audit_tables_figures_v7.py sections
python3 src/check_transport_interface.py
python3 src/edition8_calcs.py
```

`check_edition8_docs.py` verifies the visible edition labels and project-name spelling in both DOCX files, the 42 component stamps, sections 1–34, tables, captions and embedded figures. The publication cross-check and audit pass on the current combined documents. The audit also checks PNG integrity inside the DOCX files; standalone source images in `src/fig/` are not stored in the current repository, so comparisons against those files are skipped with a note.

`check_transport_interface.py` checks the 20.80 m channel against a 30.00 m opening, the 7,430.8 m route and calculated throughput. `edition8_calcs.py` recalculates the seven Edition 8 domains (A–G) and writes `src/edition8_results.json`.

**Edition 8 results that affect the model:**

- genetics: at least 5,000 founders and 200 unrelated family lines; parent exchange between cylinders of at least 1 % per generation; a gamete bank with at least 10,000 donors;
- agriculture: a 15.6 % discrepancy was found between gross and net production; losses or the source table need clarification. Reducing the protein reserve to ×1.20 frees a calculated 395 km²; the cold zone remains a major resource for multilayer cultivation;
- industry: with 5 % exposed metal, the corrosion stream is estimated at 12.17 million tonnes of steel and 5.23 million tonnes of oxygen per year; coatings reduce the corrosion-rate estimate tenfold;
- docking: under the stated quarantine model, required quarantine capacity is the limiting factor;
- ecosystem: the model uses 6,000 cats and separately accounts for 320,000 bumblebee colonies for greenhouse pollination;
- cities: twenty cities of 50,000 people are considered, together with a 1:100 virtual twin.

These are model calculations, not station certification or proof of technological readiness.

### Building the publication

`tools/combine_sections.py` assembles language-specific DOCX files from **43 bilingual source DOCX components**, preserving tables and figures:

```bash
python3 tools/combine_sections.py --src /path/to/43-component-docx --out-dir sections --language both
```

The source components are not in the current working tree; `sections/` contains the final combined documents. Rebuilding requires the source DOCX files. The script rejects the combined outputs as component input.

### Website

Website sources are in `site/`. Each published page is a self-contained HTML file with its CSS, script and required illustrations embedded. The builder creates 14 pages (7 Russian and 7 English) in `site/ru/` and `site/en/`, then syncs them to the root `ru/` and `en/` directories:

```bash
python3 site/build_pages.py
```

Home pages include a button to switch between Russian and English. Full-page menus and pagers stay within the current language. Contact pages include the shared navigation header and localized footer, but no pager. Navigation remains visible without JavaScript.

`ru/title.html` and `site/ru/title.html` are legacy build files outside the current 14-page set. They are not rebuilt or deleted; their displayed project name has also been updated to the current spelling.

### Repository contents

- `sections/` — the two final combined Edition 8 DOCX files.
- `src/` — calculations and documentation checks.
- `tools/` — document, image and local utility scripts.
- `site/content/`, `site/css/`, `site/js/` — page sources and styling.
- `site/assets/fig_ru/`, `site/assets/fig_en/` — final Russian and English gallery illustrations.
- `ru/`, `en/` — published HTML pages for GitHub Pages.
- `MMOSON_supplement_new_domains.docx` — archived document for sections 20–27; their current text is also included in the combined Edition 8 files.

### Author and status

**Roman Sergeevich Bugaenko** is the author of the personal MMOSO'N project. The project’s partner in the technological aspect is the Youth Public Movement “Interregional Cartographic Ya-Cluster” (official Russian name: Молодёжное общественное движение «Межрегиональный картографический Я-кластер», abbreviated МХ «КРЯК»). This is a conceptual research publication, not working design documentation or a flight-ready project.

The materials are provided under an **“All rights reserved / Все права защищены”** notice. Public reading is permitted; other uses require the author’s prior written consent.
