# ММОСО’Н / MMOSON

## Русская версия

**Модуль моделирования орбитальной станции О’Нилла**

Расчётная модель обитаемой орбитальной станции цилиндрического типа для точки L1 системы Земля — Солнце.

ММОСО’Н — личный инженерный и научно-исследовательский проект автора.

### Основные параметры

| Величина | Значение |
|---|---|
| Радиус цилиндра | 5 000 м |
| Длина цилиндрической части | 40 км (полная 49 км) |
| Число цилиндров | 2, встречного вращения |
| Угловая скорость | 0,04429 рад/с — 0,423 об/мин |
| Тяжесть на ободе | 1,0 g |
| Материал оболочки | сталь 18Ni(300), пояс 850 мм |
| Полная площадь | 3 100,2 км² (1 550,1 на цилиндр) |
| Масса станции | 46,70 млрд т |
| Население | 1 000 000 человек |
| Электрическая мощность | 721,4 ГВт |
| Место размещения | точка L1 Земля — Солнце |

Освещение — только реакторное, через осевые светотепловые балки. Зеркал и солнечного паруса у станции нет.

### Состав проекта

| Файл | Содержание |
|---|---|
| `sections/` | объединённые документы публикации: 2 файла — русский и английский вариант полного текста всех 43 разделов (разделы 1–34, вводные части, приложения и лицензия) |
| `sections/MMOSON_combined_document_ru.docx` | полный текст публикации на русском языке, все 43 раздела в одном файле |
| `sections/MMOSON_combined_document_en.docx` | полный текст публикации на английском языке, все 43 раздела в одном файле |
| `src/` | генераторы документа и расчётная верификация |
| `resource_map.png`, `resource_map.pdf` | ресурсная карта программы |
| `MMOSON_supplement_new_domains.docx` | архивная копия дополнения: семь новых областей анализа (разделы 20–27); текст этих разделов входит в публикацию |
| `fig/` | иллюстрации и графики публикации |

Единые монолитные файлы `MMOSON_russian_publication.docx` и `MMOSON_english_publication.docx` удалены: публикация существует только в виде раздельных документов каталога `sections/`.

### Проверка расчётов

```bash
cd src
python3 verify_all.py
python3 crosscheck.py ../sections
python3 audit_tables_figures_v7.py ../sections
```

`verify_all.py` пересчитывает величины независимо. `crosscheck.py` и `audit_tables_figures_v7.py` принимают либо один DOCX, либо каталог: им передаётся каталог `sections/` с объединёнными документами (`sections/MMOSON_combined_document_ru.docx` и `sections/MMOSON_combined_document_en.docx`), поэтому сверка охватывает всю публикацию сразу.

Новые области анализа (разделы 20–27) считаются отдельным скриптом:

```bash
cd src
python3 supplement_calcs.py          # разделы 20-27, результат в supplement_results.json
python3 edition8_calcs.py            # разделы 28-34, результат в edition8_results.json
```

Оба скрипта — чистый расчёт от первооснов, документы им не нужны.

Модули сборки монолитного документа (`integrate_supplement_v1.py`, `integrate_edition8_v1.py`, `build_supplement_docx.py`, `split_publication.py`) работали с едиными файлами `MMOSON_russian_publication.docx` и `MMOSON_english_publication.docx`. Эти файлы из репозитория удалены, поэтому модули сохранены как запись способа сборки публикации и в текущем составе репозитория не запускаются. Расчётные части (`supplement_calcs.py`, `edition8_calcs.py`, `verify_all.py`) от удаления не зависят.

### Объединённые документы публикации

Публикация объединена в два файла в каталоге `sections/` — русский и английский вариант полного текста всех 43 разделов (разделы 1–34, вводные части, приложения и лицензия). Каждый файл содержит титульные блоки, текст со таблицами и рисунками, списки литературы.

Состав каталога:

| Файл | Содержание |
|---|---|
| `sections/MMOSON_combined_document_ru.docx` | полный текст публикации на русском языке, все 43 раздела в одном файле |
| `sections/MMOSON_combined_document_en.docx` | полный текст публикации на английском языке, все 43 раздела в одном файле |

Рисунки русской и английской редакций побайтово совпадают.

`supplement_calcs.py` выводит все величины от первооснов: носовые купола как ограничение давления, аварийную потерю вращения, визуальную среду замкнутого мира, химию воздуха на столетия, почву как инженерный профиль, масштабирование архитектуры и связь из точки L1.

`integrate_supplement_v1.py` вносит разделы 20–27 в обе публикации перед приложением перечня сокращений (анкеры «ПРИЛОЖЕНИЕ В» и «APPENDIX C»): 35 заголовков, 120 абзацев и 14 таблиц `Table Grid` с шапкой `#DEEAF6` и кеглем 8 pt в ячейках, раздел 20 начинается с новой страницы. Повторный запуск надёжен — вставка идёт перед анкером, порядок разделов 1–19 и приложений не меняется. Оглавление в документах — поле автозаполнения: в Word оно обновляется по Ctrl+A, F9.

Редакция 8 (разделы 28–34 и список литературы) считается отдельным модулем:

```bash
cd src
python3 edition8_calcs.py            # разделы 28-34, результат в edition8_results.json
```

`edition8_calcs.py` считает восемь областей от первооснов: генетику замкнутой популяции (эффективный размер, темп инбридинга, требование к основателям, кровные браки, две субпопуляции, генетический груз, банк гамет), пересмотр и оптимизацию сельского хозяйства (пересчёт отдачи по площади, два сценария линейного программирования, многоярусное выращивание в холодной зоне), промышленный контур (коррозионный поток как главный материальный поток, потребность в новой стали, ресурсная база, энергия переработки), стыковочный модуль, кошек, насекомых и города с виртуальным двойником.

Результаты редакции 8, имеющие прямое действие на проект:

- генетика: 5 000 основателей при 200 несвязанных линиях; подбор пары до четвёртой степени родства; двоюродные сибсы запрещены; обмен родителями между цилиндрами не менее 1 % за поколение; банк гамет от 10 000 доноров;
- сельское хозяйство: обнаружена несостыковка 15,6 % между валовой продукцией посевов (2 216 млрд ккал, таблица 5.4) и продукцией нетто (1 870 трлн ккал, таблица 5.2) — требуется строка потерь либо уточнение таблицы; белковый запас ×2,73 при калорийном ×1,83 несоразен, приведение к ×1,20 высвобождает 395 км²; холодная зона 251,3 км² — крупнейший неиспользованный ресурс, 20 % её при трёх ярусах дают 16,7 % потребности в калориях; резерв быстрых культур 150 → 90 км²;
- промышленность: коррозионный поток при 5 % открытого металла (12,17 млн т стали и 5,23 млн т кислорода в год) в двадцать раз превосходит все бытовые отходы; покрытия снижают его в десять раз и являются условием кислородного баланса; астероид (6178) 1986 DA даёт 70,7 млрд т — 3,2 покрытия потребности при покрытом исполнении (0,03 без покрытий), второго источника требует неизбежно;
- стыковочный модуль: темп заселения ограничен карантином (2 597 403 места при полном темпе), а не транспортом;
- кошки: 6 000 голов, корм 92,9 т/год, животная доля 60,4 т/год, полностью покрывается отходами разделки рыбы (21 000 т/год) и мукой из личинок;
- насекомые: шмели 320 000 семей для 80 км² тепличных культур — на два порядка больше пчелиного поголовья; мука из личинок покрывает 17 % потребности в комбикорме;
- города: двадцать городов по 50 000 человек радиусом 1,38 км; виртуальный двойник в Minecraft в масштабе 1:100 (490 × 100 блоков).

`integrate_edition8_v1.py` вносит разделы 28–34 в обе публикации перед приложением перечня сокращений и список литературы перед приложением статусов: 44 заголовка, 134 абзаца, 11 таблиц `Table Grid` с шапкой `#DEEAF6` и кеглем 8 pt, раздел 28 начинается с новой страницы. Приложение литературы в русской редакции — «Приложение Д» (в нумерации Б, В, Г, Е оно отсутствовало), в английской — «Appendix F» (английская нумерация содержит APPENDIX D «Sources»). Повторный запуск идемпотентен: прежний блок удаляется перед вставкой.

### Автор

**Бугаенко Роман Сергеевич** — независимый автор и руководитель личного инженерного и научно-исследовательского проекта ММОСО’Н.

В рамках проекта автор занимается концепцией и архитектурой станции, климатическим зонированием, составом биоценозов, инженерными решениями, продовольственным и водным балансами.

**НИК** (Нить искренности в Континууме) — расчётная верификация, пересчёт прочности и балансов, оформление документа и верификация.

### Лицензия

Проект распространяется по проприетарному уведомлению **«Все права защищены / All rights reserved»**. Свободное чтение и ознакомление разрешены. Любое иное использование, копирование, распространение, перевод, переработка, публикация или включение материалов в другие проекты требует предварительного письменного согласия автора. Полные двуязычные условия находятся в `LICENCE.txt` и в документе `sections/ЛИЦЕНЗИЯ.docx`.

---

## English version

**Modeling Module for an O’Neill Orbital Station**

A calculation model of a cylindrical inhabited orbital station intended for the Earth–Sun L1 point.

MMOSON is the author’s personal engineering and research project.

### Main parameters

| Parameter | Value |
|---|---|
| Cylinder radius | 5,000 m |
| Cylindrical section length | 40 km (49 km overall) |
| Number of cylinders | 2, counter-rotating |
| Angular velocity | 0.04429 rad/s — 0.423 rpm |
| Rim gravity | 1.0 g |
| Shell material | 18Ni(300) steel, 850 mm belt |
| Total area | 3,100.2 km² (1,550.1 per cylinder) |
| Station mass | 46.70 billion tonnes |
| Population | 1,000,000 people |
| Electrical power | 721.4 GW |
| Location | Earth–Sun L1 point |

Lighting is provided only by reactors through axial light-and-thermal beams. The station has no mirrors and no solar sail.

### Project contents

| File | Contents |
|---|---|
| `sections/` | combined documents of the publication: 2 files — Russian and English variants of the full text of all 43 sections (sections 1–34, introductory parts, appendices and licence) |
| `sections/MMOSON_combined_document_ru.docx` | full publication text in Russian, all 43 sections in one file |
| `sections/MMOSON_combined_document_en.docx` | full publication text in English, all 43 sections in one file |
| `src/` | document generators and calculation verification |
| `resource_map.png`, `resource_map.pdf` | program resource map |
| `MMOSON_supplement_new_domains.docx` | archived copy of the supplement: seven new analysis domains (sections 20–27); the text of these sections is part of the publication |
| `fig/` | publication figures and charts |

The single monolithic files `MMOSON_russian_publication.docx` and `MMOSON_english_publication.docx` have been removed: the publication exists only as the separate documents of the `sections/` directory.

### Calculation checks

```bash
cd src
python3 verify_all.py
python3 crosscheck.py ../sections
python3 audit_tables_figures_v7.py ../sections
```

`verify_all.py` independently recalculates the values. `crosscheck.py` and `audit_tables_figures_v7.py` accept either a single DOCX or a directory: the `sections/` directory is passed with the combined documents (`sections/MMOSON_combined_document_ru.docx` and `sections/MMOSON_combined_document_en.docx`), so the check covers the entire publication at once.

The new analysis domains (sections 20–27) are computed by a separate script:

```bash
cd src
python3 supplement_calcs.py          # sections 20-27, output in supplement_results.json
python3 edition8_calcs.py            # sections 28-34, output in edition8_results.json
```

Both scripts are pure first-principles calculation and need no documents.

The document-assembly modules (`integrate_supplement_v1.py`, `integrate_edition8_v1.py`, `build_supplement_docx.py`, `split_publication.py`) operated on the single files `MMOSON_russian_publication.docx` and `MMOSON_english_publication.docx`. Those files have been removed from the repository, so the modules are kept as a record of how the publication was assembled and do not run against the current repository contents. The calculation parts (`supplement_calcs.py`, `edition8_calcs.py`, `verify_all.py`) do not depend on that removal.

### Combined documents of the publication

The publication is combined into two files in the `sections/` directory — Russian and English variants of the full text of all 43 sections (sections 1–34, introductory parts, appendices and licence). Each file contains title blocks, text with tables and figures, and reference lists.

Contents of the directory:

| File | Contents |
|---|---|
| `sections/MMOSON_combined_document_ru.docx` | full publication text in Russian, all 43 sections in one file |
| `sections/MMOSON_combined_document_en.docx` | full publication text in English, all 43 sections in one file |

The figures of the Russian and English editions are byte-identical.

`supplement_calcs.py` derives every value from first principles: nose domes as a pressure boundary, emergency loss of rotation, the visual environment of a closed world, air chemistry over centuries, soil as an engineered profile, architecture scaling, and communications from the L1 point.

`integrate_supplement_v1.py` merges sections 20–27 into both publications just before the appendix listing abbreviations (anchors `ПРИЛОЖЕНИЕ В` and `APPENDIX C`): 35 headings, 120 paragraphs and 14 `Table Grid` tables with a `#DEEAF6` header row and 8 pt text in the cells, section 20 starting on a new page. The run is idempotent — a previously merged block is removed first, so the order of sections 1–19 and of the appendices is preserved. The tables of contents in the documents are fields: Word refreshes them with Ctrl+A, F9.

Edition 8 (sections 28–34 and the reference list) is computed by a separate module:

```bash
cd src
python3 edition8_calcs.py            # sections 28-34, output in edition8_results.json
```

`edition8_calcs.py` computes the eight new domains from first principles: genetics of a closed population (effective size, rate of inbreeding, founder requirement, consanguineous marriages, two subpopulations, genetic load, gamete bank), the review and optimisation of agriculture (recomputation of yield per area, two linear-programming scenarios, multilayer cultivation in the cold zone), the industrial circuit (the corrosion stream as the dominant material flow, demand for new steel, resource base, processing energy), the docking module, cats, insects, and cities with a virtual twin.

Edition 8 results that bear directly on the project:

- genetics: 5,000 founders with 200 unrelated family lines; mate selection up to the fourth degree of relationship; first-cousin sibs forbidden; parent exchange between cylinders not below 1 % per generation; a gamete bank of 10,000 donors;
- agriculture: a 15.6 % inconsistency is found between gross crop production (2,216 billion kcal, Table 5.4) and net production (1,870 trillion kcal, Table 5.2) — either a loss line or a refined Table 5.2 is required; the protein surplus of ×2.73 against a calorie ×1.83 is disproportionate, and bringing it to ×1.20 frees 395 km²; the cold zone of 251.3 km² is the largest unused resource, with 20 % of it at three layers giving 16.7 % of calorie need; the fast-crop reserve 150 → 90 km²;
- industry: the corrosion stream at 5 % exposed metal (12.17 million t of steel and 5.23 million t of oxygen per year) is twenty times all domestic waste; coatings cut it tenfold and are a condition of the oxygen balance; asteroid (6178) 1986 DA gives 70.7 billion t — 3.2 coverings of demand in coated execution (0.03 without coatings), so a second source is unavoidable;
- docking module: the pace of settlement is limited by quarantine (2,597,403 places at full pace), not by transport;
- cats: 6,000 head, feed 92.9 t/yr, animal fraction 60.4 t/yr, fully covered by fish-dressing waste (21,000 t/yr) and larval meal;
- insects: 320,000 bumblebee colonies for 80 km² of greenhouse crops — two orders of magnitude above the bee number; larval meal covers 17 % of compound-feed requirement;
- cities: twenty cities of 50,000 people with a radius of 1.38 km; a virtual twin in Minecraft at 1:100 (490 × 100 blocks).

`integrate_edition8_v1.py` merges sections 28–34 into both publications just before the appendix listing abbreviations, and the reference list just before the status-matrix appendix: 44 headings, 134 paragraphs and 11 `Table Grid` tables with a `#DEEAF6` header row and 8 pt text in the cells, section 28 starting on a new page. The references appendix is Appendix Д in the Russian edition (the numbering Б, В, Г, Е left no Д) and Appendix F in the English edition (whose numbering already contains APPENDIX D «Sources»). The run is idempotent — a previously merged block is removed first.

### Author

**Roman Sergeevich Bugaenko** is an independent author and the lead of the personal MMOSON engineering and research project.

Within MMOSON, the author works on the station concept and architecture, climate zoning, biocenosis composition, engineering solutions, and food and water balances.

**NIK** (*Thread of Sincerity in the Continuum*) performs calculation verification, strength and balance recalculation, and document preparation and verification.

### Licence

The project is distributed under a proprietary **“All rights reserved / Все права защищены”** notice. Public reading and review are permitted. Any other use, copying, distribution, translation, adaptation, publication or incorporation of materials into other projects requires the author’s prior written permission. The complete bilingual terms are provided in `LICENCE.txt` and in `sections/ЛИЦЕНЗИЯ.docx`.

---

## Project status / Статус проекта

This is a conceptual research publication, not a flight-ready design or an approved operational construction package. / Это концептуальная научно-исследовательская публикация, а не готовый к полёту проект и не утверждённая рабочая конструкторская документация.
