#!/usr/bin/env python3
"""Генерация красивых иллюстраций галереи ММОСО'Н на русском и английском.

Стиль: тёмный космический фон, звёзды, цветные геометрические иллюстрации,
информационные панели с параметрами станции. Разрешение 1200x675.

Параметры станции (по документации):
  * Два встречно вращающихся цилиндра, радиус 5 000 м
  * Длина цилиндрической части 40 км (полная 49 км)
  * Угловая скорость 0,04429 рад/с (0,423 об/мин), тяжесть на ободе 1,0 g
  * Освещение только реакторное через осевые светотепловые балки
  * Без солнечных зеркал и паруса
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RU_DIR = Path("site/assets/fig")
EN_DIR = Path("site/assets/fig_en")
RU_DIR.mkdir(parents=True, exist_ok=True)
EN_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1200, 675

# ═══ ЦВЕТА ═══
C_BG_TOP = (8, 12, 24)      # тёмно-синий (космос)
C_BG_BOT = (0, 0, 0)        # чёрный
C_STAR = (240, 240, 245)
C_TEXT = (235, 240, 245)
C_TITLE = (255, 255, 255)
C_SUB = (160, 175, 195)
C_PANEL_BG = (20, 28, 44, 225)
C_PANEL_LINE = (70, 100, 140)
C_ACCENT = (255, 190, 90)   # золото
C_CYL1 = (100, 150, 220)    # синий цилиндр
C_CYL2 = (220, 120, 90)     # оранжевый цилиндр
C_AXIS = (140, 180, 255)    # ось
C_GRID = (60, 80, 110)

try:
    F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    F_SUB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    F_PARAM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
    F_PARAM_BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
    F_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    F_TITLE = ImageFont.load_default()
    F_SUB = ImageFont.load_default()
    F_PARAM = ImageFont.load_default()
    F_PARAM_BOLD = ImageFont.load_default()
    F_SMALL = ImageFont.load_default()


def gradient_bg(img: Image.Image) -> None:
    """Градиентный фон космоса + звёзды."""
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(C_BG_TOP[0] * (1 - t) + C_BG_BOT[0] * t)
        g = int(C_BG_TOP[1] * (1 - t) + C_BG_BOT[1] * t)
        b = int(C_BG_TOP[2] * (1 - t) + C_BG_BOT[2] * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # Звёзды
    rng = random.Random(42)
    for _ in range(300):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, int(H * 0.75))
        b = rng.randint(150, 255)
        d.point([(x, y)], fill=(b, b, b))


def draw_title(d: ImageDraw.Draw, title_ru: str, title_en: str, lang: str) -> int:
    title = title_ru if lang == "ru" else title_en
    tw = d.textlength(title, font=F_TITLE)
    d.text(((W - tw) / 2, 24), title, font=F_TITLE, fill=C_TITLE)
    return 72


def draw_panel(d: ImageDraw.Draw, x: int, y: int, w: int, h: int,
               lines: list[tuple[str, str]], lang: str) -> None:
    """Полупрозрачная панель с параметрами справа."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=C_PANEL_BG,
                        outline=C_PANEL_LINE, width=2)
    px = x + 24
    py = y + 20
    for label, value in lines:
        # метка
        d.text((px, py), label, font=F_PARAM, fill=C_SUB)
        # значение (правее)
        vw = d.textlength(value, font=F_PARAM_BOLD)
        d.text((x + w - 24 - vw, py), value, font=F_PARAM_BOLD, fill=C_TEXT)
        py += 30
    d.text((px, py + 10), "", font=F_SMALL)


def draw_cylinder(d: ImageDraw.Draw, cx: int, cy: int, r: int, color: tuple,
                  angle_deg: float = 0, width: int = 5) -> None:
    """Рисует цилиндр в проёме (эллипс + боковые линии)."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)
    # внутренний контур
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8],
              outline=(int(color[0] * 0.6), int(color[1] * 0.6), int(color[2] * 0.6)),
              width=2)
    # ось
    d.line([(cx, cy - r), (cx, cy + r)], fill=C_AXIS, width=2)


def save(img: Image.Image, ru_path: Path, en_path: Path) -> None:
    img.convert("RGB").save(ru_path, "PNG")
    img.convert("RGB").save(en_path, "PNG")
    print(f"  {ru_path.name}")


# ═════════════════════════════════════════════════════════════════════════════
# 01. Компоновка станции — из 3D рендера (уже готова)
# ═════════════════════════════════════════════════════════════════════════════
def make_fig01() -> None:
    from shutil import copy2
    copy2("site/assets/fig/fig01_layout.png", "site/assets/fig_en/fig01_layout.png")
    print("  fig01_layout (из 3D рендера)")


# ═════════════════════════════════════════════════════════════════════════════
# 02. Разрез станции
# ═════════════════════════════════════════════════════════════════════════════
def make_fig02(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Разрез станции: поперечный и продольный вид",
                   "Station section: cross-section and longitudinal view", lang)

    cx, cy = 380, 360
    r = 130
    # 外壳
    draw_cylinder(d, cx, cy, r, C_CYL1)
    # перегородки
    d.line([(cx - r, cy), (cx + r, cy)], fill=C_GRID, width=2)
    d.line([(cx, cy - r), (cx, cy + r)], fill=C_GRID, width=2)
    # внутренняя оболочка
    d.ellipse([cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22],
              outline=C_CYL2, width=3)
    # подписи частей
    d.text((cx + r + 16, cy - 60), "оболочка / envelope", font=F_SMALL, fill=C_TEXT)
    d.text((cx + r + 16, cy - 30), "перегородки / partitions", font=F_SMALL, fill=C_TEXT)
    d.text((cx + r + 16, cy), "ось / axis", font=F_SMALL, fill=C_TEXT)

    px = 560
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Оболочка / Envelope:", "сталь 18Ni(300), пояс 850 мм" if lang == "ru"
         else "steel 18Ni(300), belt 850 mm"),
        ("Перегородки / Partitions:", "климатические зоны" if lang == "ru"
         else "climatic zones"),
        ("Ось / Axis:", "светотепловая балка" if lang == "ru"
         else "light-heat beam"),
    ], lang)
    save(img, RU_DIR / "fig02_section.png", EN_DIR / "fig02_section.png")


# ═════════════════════════════════════════════════════════════════════════════
# 03. Искусственная гравитация
# ═════════════════════════════════════════════════════════════════════════════
def make_fig03(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Искусственная гравитация станции",
                   "Station artificial gravity", lang)

    cx, cy = 340, 360
    r = 140
    draw_cylinder(d, cx, cy, r, C_CYL1)
    # стрелка гравитации (вниз от обода к центру)
    d.line([(cx + r, cy), (cx + int(r * 0.75), cy)], fill=C_ACCENT, width=6)
    d.polygon([(cx + int(r * 0.75), cy - 10), (cx + int(r * 0.75), cy + 10),
               (cx + r + 8, cy)], fill=C_ACCENT)
    d.text((cx + r + 16, cy - 14), "1,0 g" if lang == "ru" else "1.0 g",
           font=F_TITLE, fill=C_TEXT)

    px = 560
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Ускорение / Acceleration:", "1,0 g" if lang == "ru" else "1.0 g"),
        ("Радиус / Radius:", "5 000 м" if lang == "ru" else "5 000 m"),
        ("Угл. скорость / Ang. vel.:", "0,04429 рад/с" if lang == "ru"
         else "0.04429 rad/s"),
    ], lang)
    save(img, RU_DIR / "fig03_gravity.png", EN_DIR / "fig03_gravity.png")


# ═════════════════════════════════════════════════════════════════════════════
# 04. Климатические зоны
# ═════════════════════════════════════════════════════════════════════════════
def make_fig04(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Климатические зоны цилиндра",
                   "Climatic zones of the cylinder", lang)

    cx, cy = 300, 360
    zones = [
        (0, 10, "тропическая / Tropical", (255, 140, 60)),
        (10, 22, "субтропическая / Subtr.", (255, 200, 80)),
        (22, 32, "умеренная / Moderate", (120, 200, 120)),
        (32, 40, "холодная / Cold", (120, 160, 220)),
    ]
    z_h = 70
    for i, (km0, km1, name, col) in enumerate(zones):
        yy = cy - 140 + i * (z_h + 12)
        d.rounded_rectangle([cx - 140, yy, cx + 140, yy + z_h], radius=8,
                            fill=(*col, 60), outline=col, width=3)
        d.text((cx - 125, yy + 16), f"{km0}–{km1} км / km", font=F_PARAM, fill=C_TEXT)
        d.text((cx - 125, yy + 42), name, font=F_SMALL, fill=C_SUB)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 300, [
        ("Тропическая / Tropical:", "0–10 км / km" if lang == "ru" else "0–10 km"),
        ("Субтропич. / Subtr.:", "10–22 км / km" if lang == "ru" else "10–22 km"),
        ("Умеренная / Moderate:", "22–32 км / km" if lang == "ru" else "22–32 km"),
        ("Холодная / Cold:", "32–40 км / km" if lang == "ru" else "32–40 km"),
    ], lang)
    save(img, RU_DIR / "fig04_climate.png", EN_DIR / "fig04_climate.png")


# ═════════════════════════════════════════════════════════════════════════════
# 05. Давление
# ═════════════════════════════════════════════════════════════════════════════
def make_fig05(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Атмосферное давление станции",
                   "Station atmospheric pressure", lang)

    cx, cy = 340, 360
    r = 110
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=C_CYL1, width=6)
    d.ellipse([cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20],
              outline=C_CYL2, width=3)
    d.line([(cx, cy - r), (cx, cy + r)], fill=C_AXIS, width=2)
    val = "101,3 кПа" if lang == "ru" else "101.3 kPa"
    tw = d.textlength(val, font=F_TITLE)
    d.text((cx - tw / 2, cy - 20), val, font=F_TITLE, fill=C_TEXT)
    d.text((cx - 70, cy + 40), "оболочка / envelope", font=F_SMALL, fill=C_SUB)

    px = 560
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Давление / Pressure:", val),
        ("Состав / Composition:", "N₂ 78 % · O₂ 21 % · 1 %"),
        ("Избыточное / Excess:", "не более 5 кПа" if lang == "ru"
         else "not more than 5 kPa"),
    ], lang)
    save(img, RU_DIR / "fig05_pressure.png", EN_DIR / "fig05_pressure.png")


# ═════════════════════════════════════════════════════════════════════════════
# 06. Сталь
# ═════════════════════════════════════════════════════════════════════════════
def make_fig06(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Структурная сталь 18Ni(300)",
                   "Structural steel 18Ni(300)", lang)

    cx, cy = 340, 360
    # образец стального пояса
    d.rounded_rectangle([cx - 110, cy - 70, cx + 110, cy + 70], radius=16,
                        fill=(90, 100, 110), outline=C_CYL1, width=4)
    d.text((cx - 60, cy - 24), "18Ni(300)", font=F_TITLE, fill=C_TEXT)
    d.text((cx - 60, cy + 20), "850 мм / mm", font=F_PARAM, fill=C_SUB)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 260, [
        ("Прочность / Tensile:", "1 200 МПа" if lang == "ru" else "1 200 MPa"),
        ("Плотность / Density:", "7 850 кг/м³" if lang == "ru" else "7 850 kg/m³"),
        ("Пояс / Belt:", "850 мм / mm"),
        ("Источник / Source:", "астероид 6178" if lang == "ru"
         else "asteroid 6178"),
    ], lang)
    save(img, RU_DIR / "fig06_steel.png", EN_DIR / "fig06_steel.png")


# ═════════════════════════════════════════════════════════════════════════════
# 07. Нагрузки
# ═════════════════════════════════════════════════════════════════════════════
def make_fig07(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Динамические нагрузки на конструкции",
                   "Dynamic loads on station structures", lang)

    cx, cy = 340, 360
    draw_cylinder(d, cx, cy, 100, C_CYL1)
    # стрелы нагрузок
    d.line([(cx - 100, cy - 60), (cx - 140, cy - 60)], fill=C_ACCENT, width=5)
    d.line([(cx + 100, cy - 60), (cx + 140, cy - 60)], fill=C_ACCENT, width=5)
    d.line([(cx, cy + 100), (cx, cy + 140)], fill=C_ACCENT, width=5)
    d.text((cx - 150, cy - 80), "ц Centre." if lang == "ru" else "centrif.",
           font=F_SMALL, fill=C_ACCENT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Цилиндры / Cylinders:", "центробежные" if lang == "ru"
         else "centrifugal"),
        ("Рама / Frame:", "статические от причалов" if lang == "ru"
         else "static from docks"),
        ("Опорный узел / Node:", "в пределах нормы" if lang == "ru"
         else "within design limit"),
    ], lang)
    save(img, RU_DIR / "fig07_load.png", EN_DIR / "fig07_load.png")


# ═════════════════════════════════════════════════════════════════════════════
# 08. Масса
# ═════════════════════════════════════════════════════════════════════════════
def make_fig08(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Масса станции по элементам",
                   "Station mass by elements", lang)

    cx, cy = 340, 360
    # круговая диаграмма
    d.pieslice([cx - 90, cy - 90, cx + 90, cy + 90], -90, 338.4,
               fill=C_CYL1, outline=(255, 255, 255), width=3)
    d.pieslice([cx - 90, cy - 90, cx + 90, cy + 90], 338.4, 360,
               fill=C_ACCENT, outline=(255, 255, 255), width=3)
    d.pieslice([cx - 90, cy - 90, cx + 90, cy + 90], 360, 369,
               fill=(120, 140, 170), outline=(255, 255, 255), width=3)
    d.pieslice([cx - 90, cy - 90, cx + 90, cy + 90], 369, 378,
               fill=(180, 100, 80), outline=(255, 255, 255), width=3)
    d.text((cx - 30, cy - 10), "94 %" if lang == "ru" else "94 %",
           font=F_TITLE, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 260, [
        ("Общая масса / Total:", "46,70 млрд т" if lang == "ru"
         else "46.70 billion t"),
        ("Конструкции / Structural:", "94 %"),
        ("Жизнеобеспеч. / Life sup.:", "3,5 %" if lang == "ru" else "3.5 %"),
        ("Оборудование / Equipm.:", "2,5 %" if lang == "ru" else "2.5 %"),
    ], lang)
    save(img, RU_DIR / "fig08_mass.png", EN_DIR / "fig08_mass.png")


# ═════════════════════════════════════════════════════════════════════════════
# 09. Тепловой баланс
# ═════════════════════════════════════════════════════════════════════════════
def make_fig09(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Тепловой баланс станции",
                   "Station thermal balance", lang)

    cx, cy = 340, 360
    draw_cylinder(d, cx, cy, 90, C_CYL1)
    # радиаторы по бокам
    d.rectangle([cx - 130, cy - 40, cx - 100, cy + 40], fill=C_ACCENT)
    d.rectangle([cx + 100, cy - 40, cx + 130, cy + 40], fill=C_ACCENT)
    d.text((cx - 120, cy + 55), "радиаторы" if lang == "ru" else "radiators",
           font=F_SMALL, fill=C_ACCENT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Источники / Sources:", "реакторы, оборуд., люди" if lang == "ru"
         else "reactors, equip., people"),
        ("Отвод / Rejection:", "радиаторные панели" if lang == "ru"
         else "radiator panels"),
        ("Меж цилиндрами / Between:", "нет / none" if lang == "ru" else "none"),
    ], lang)
    save(img, RU_DIR / "fig09_thermal.png", EN_DIR / "fig09_thermal.png")


# ═════════════════════════════════════════════════════════════════════════════
# 10. Энергетика
# ═════════════════════════════════════════════════════════════════════════════
def make_fig10(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Баланс энергии станции",
                   "Station energy balance", lang)

    cx, cy = 340, 360
    # реактор
    d.rounded_rectangle([cx - 80, cy - 80, cx + 80, cy + 80], radius=16,
                        fill=C_CYL1, outline=C_ACCENT, width=4)
    d.text((cx - 40, cy - 20), "реактор" if lang == "ru" else "reactor",
           font=F_PARAM, fill=C_TEXT)
    val = "721,4 ГВт" if lang == "ru" else "721.4 GW"
    tw = d.textlength(val, font=F_PARAM_BOLD)
    d.text((cx - tw / 2, cy + 25), val, font=F_PARAM_BOLD, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Источники / Sources:", "ядерные реакторы" if lang == "ru"
         else "nuclear reactors"),
        ("Мощность / Power:", val),
        ("Распределение / Distrib.:", "ЖО, произ-во, климат" if lang == "ru"
         else "life supp., prod., clim."),
    ], lang)
    save(img, RU_DIR / "fig10_energy.png", EN_DIR / "fig10_energy.png")


# ═════════════════════════════════════════════════════════════════════════════
# 11. Стыковка
# ═════════════════════════════════════════════════════════════════════════════
def make_fig11(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Система стыковки станции",
                   "Station docking system", lang)

    cx, cy = 340, 360
    d.rounded_rectangle([cx - 110, cy - 50, cx + 110, cy + 50], radius=12,
                        fill=(*C_CYL1, 40), outline=C_CYL1, width=4)
    d.line([(cx, cy - 50), (cx, cy + 50)], fill=C_AXIS, width=3)
    d.text((cx - 30, cy - 14), "причал / dock", font=F_SMALL, fill=C_TEXT)
    d.text((cx - 30, cy + 14), "ось / axis", font=F_SMALL, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 200, [
        ("Причалы / Docks:", "цилиндр + рама" if lang == "ru"
         else "cylinder + frame"),
        ("Переход / Transition:", "через ось" if lang == "ru" else "via axis"),
    ], lang)
    save(img, RU_DIR / "fig11_docking.png", EN_DIR / "fig11_docking.png")


# ═════════════════════════════════════════════════════════════════════════════
# 12. Кориолис
# ═════════════════════════════════════════════════════════════════════════════
def make_fig12(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Силы Кориолиса на станции",
                   "Coriolis forces on station", lang)

    cx, cy = 340, 360
    draw_cylinder(d, cx, cy, 100, C_CYL1)
    # спираль Кориолиса
    for i in range(20):
        a = i * 0.35
        rr = 30 + i * 3
        x = cx + rr * math.cos(a)
        yy = cy + rr * math.sin(a)
        d.point([(x, yy)], fill=C_ACCENT)
    d.text((cx + 110, cy - 10), "Coriolis / Кориолис", font=F_SMALL, fill=C_ACCENT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Угл. скорость / Ang. vel.:", "0,04429 рад/с" if lang == "ru"
         else "0.04429 rad/s"),
        ("Отклонение / Deflection:", "при радиальном движ." if lang == "ru"
         else "during radial move"),
        ("Компенсация / Comp.:", "навигация, управление" if lang == "ru"
         else "navigation, control"),
    ], lang)
    save(img, RU_DIR / "fig12_coriolis.png", EN_DIR / "fig12_coriolis.png")


# ═════════════════════════════════════════════════════════════════════════════
# 13. Подъем по радиусу
# ═════════════════════════════════════════════════════════════════════════════
def make_fig13(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Подъем по радиусу цилиндра",
                   "Climb along cylinder radius", lang)

    cx, cy = 340, 360
    r = 100
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=C_CYL1, width=5)
    d.line([(cx, cy), (cx, cy - r)], fill=C_ACCENT, width=4)
    d.text((cx + 12, cy - r - 20), "0 g → 1 g", font=F_PARAM_BOLD, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Гравитация / Gravity:", "меняется с радиусом" if lang == "ru"
         else "changes with radius"),
        ("Центр → обод / Center→Rim:", "0 g → 1 g"),
        ("Ограничения / Limits:", "тяжёлая техника" if lang == "ru"
         else "heavy equipment"),
    ], lang)
    save(img, RU_DIR / "fig13_climb.png", EN_DIR / "fig13_climb.png")


# ═════════════════════════════════════════════════════════════════════════════
# 14. Падение
# ═════════════════════════════════════════════════════════════════════════════
def make_fig14(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Падение на станции",
                   "Fall on station", lang)

    cx, cy = 340, 360
    draw_cylinder(d, cx, cy, 90, C_CYL1)
    # траектория падения (кривая)
    pts = []
    for i in range(40):
        t = i / 39
        x = cx - 60 + 120 * t
        yy = cy - 40 + 80 * t - 60 * t * t
        pts.append((x, yy))
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=C_ACCENT, width=3)
    d.text((pts[-1][0] + 8, pts[-1][1]), "траектория" if lang == "ru"
           else "trajectory", font=F_SMALL, fill=C_ACCENT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Траектория / Trajectory:", "вращающийся фрейм" if lang == "ru"
         else "rotating frame"),
        ("Кориолис / Coriolis:", "влияние на траекторию" if lang == "ru"
         else "effect on trajectory"),
        ("Безопасность / Safety:", "внутри цилиндра" if lang == "ru"
         else "inside cylinder"),
    ], lang)
    save(img, RU_DIR / "fig14_fall.png", EN_DIR / "fig14_fall.png")


# ═════════════════════════════════════════════════════════════════════════════
# 15. Транспортный маршрут
# ═════════════════════════════════════════════════════════════════════════════
def make_fig15(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Маршрут от дока к поверхности",
                   "Route from dock to habitable surface", lang)

    steps_ru = [
        "1. Кабельная оболочка → рама",
        "2. Опорный узел → вращение",
        "3. Тепловой барьер",
        "4. Корпус в тороиде",
        "5. Осевая балка",
        "6. Слой гравитации 1 000 г",
        "7. Производств. зона (закрыта)",
    ]
    steps_en = [
        "1. Cable fairing → frame",
        "2. Support node → rotation",
        "3. Thermal barrier",
        "4. Hull in toroid",
        "5. Axial beam",
        "6. Gravity layer 1 000 g",
        "7. Prod. zone (closed)",
    ]
    steps = steps_ru if lang == "ru" else steps_en
    yy = 200
    for s in steps:
        d.rounded_rectangle([100, yy, 420, yy + 40], radius=10,
                            fill=(*C_CYL1, 50), outline=C_CYL1, width=3)
        d.text((115, yy + 10), s, font=F_PARAM, fill=C_TEXT)
        if yy < 500:
            d.line([(260, yy + 40), (260, yy + 52)], fill=C_AXIS, width=3)
        yy += 52

    save(img, RU_DIR / "fig15_transport.png", EN_DIR / "fig15_transport.png")


# ═════════════════════════════════════════════════════════════════════════════
# 16. Ресурсы
# ═════════════════════════════════════════════════════════════════════════════
def make_fig16(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Потребность в материалах",
                   "Material requirement", lang)

    items_ru = [
        ("Сталь 18Ni(300)", "астероид 6178 1986 DA", C_CYL1),
        ("Реголит", "переработка", C_CYL2),
        ("Дышащая смесь", "N₂, O₂", (100, 180, 220)),
        ("Борид карбида", "твердый", (180, 120, 80)),
        ("Вода", "концепт", (120, 160, 220)),
        ("Теплоизоляция", "оболочка", (160, 160, 170)),
    ]
    items_en = [
        ("Steel 18Ni(300)", "asteroid 6178 1986 DA", C_CYL1),
        ("Regolith", "reprocessing", C_CYL2),
        ("Breathable mix", "N2, O2", (100, 180, 220)),
        ("Boron carbide", "hard", (180, 120, 80)),
        ("Water", "concept", (120, 160, 220)),
        ("Thermal insulation", "shell", (160, 160, 170)),
    ]
    items = items_ru if lang == "ru" else items_en
    yy = 180
    for name, sub, col in items:
        d.rounded_rectangle([100, yy, 420, yy + 50], radius=10,
                            fill=(*col, 50), outline=col, width=3)
        d.text((115, yy + 8), name, font=F_PARAM_BOLD, fill=C_TEXT)
        d.text((115, yy + 28), sub, font=F_SMALL, fill=C_SUB)
        yy += 58

    save(img, RU_DIR / "fig16_resources.png", EN_DIR / "fig16_resources.png")


# ═════════════════════════════════════════════════════════════════════════════
# 17. Питание
# ═════════════════════════════════════════════════════════════════════════════
def make_fig17(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Система питания станции",
                   "Station food system", lang)

    # грядки
    d.rectangle([120, 280, 300, 420], fill=(60, 120, 60), outline=(100, 180, 100), width=3)
    d.text((135, 340), "растения" if lang == "ru" else "plants", font=F_PARAM, fill=C_TEXT)
    # пруды
    d.ellipse([330, 280, 460, 380], fill=(60, 100, 160), outline=(100, 150, 220), width=3)
    d.text((350, 320), "рыбоводство" if lang == "ru" else "aquaculture",
           font=F_PARAM, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Зоны / Zones:", "сельхоз, рис, грибы" if lang == "ru"
         else "agri, rice, fungi"),
        ("Рыбоводство / Aqua:", "пруды, платформы" if lang == "ru"
         else "ponds, platforms"),
        ("Циклы / Cycles:", "биомасса" if lang == "ru" else "biomass"),
    ], lang)
    save(img, RU_DIR / "fig17_food.png", EN_DIR / "fig17_food.png")


# ═════════════════════════════════════════════════════════════════════════════
# 18. Использование земли
# ═════════════════════════════════════════════════════════════════════════════
def make_fig18(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Использование земли двух цилиндров",
                   "Land use of two cylinders", lang)

    cx, cy = 300, 360
    r = 90
    # круговая диаграмма землепользования
    d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, 194.4,
               fill=C_CYL1, outline=(255, 255, 255), width=3)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 194.4, 324,
               fill=C_ACCENT, outline=(255, 255, 255), width=3)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 324, 360,
               fill=(120, 140, 170), outline=(255, 255, 255), width=3)
    d.text((cx - 25, cy - 10), "54 %" if lang == "ru" else "54 %",
           font=F_TITLE, fill=C_TEXT)

    px = 520
    draw_panel(d, px, 110, W - px - 24, 280, [
        ("Биосфера / Biosphere:", "1 550,1 км²" if lang == "ru" else "1 550.1 km²"),
        ("Посевные / Sowing:", "807 км² · 54 %" if lang == "ru"
         else "807 km² · 54 %"),
        ("Резерв / Reserve:", "536 км² · 36 %" if lang == "ru"
         else "536 km² · 36 %"),
        ("Пруды / Ponds:", "15 км² · 1 %" if lang == "ru" else "15 km² · 1 %"),
    ], lang)
    save(img, RU_DIR / "fig18_land.png", EN_DIR / "fig18_land.png")


# ═════════════════════════════════════════════════════════════════════════════
# 19. Эпидемия / Карантин
# ═════════════════════════════════════════════════════════════════════════════
def make_fig19(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Система карантина и эпидемиологической безопасности",
                   "Station quarantine and epidemiological safety", lang)

    cx, cy = 340, 360
    d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100],
              fill=(*C_CYL1, 40), outline=C_CYL1, width=4)
    d.line([(cx - 70, cy - 70), (cx + 70, cy + 70)], fill=C_ACCENT, width=4)
    d.line([(cx + 70, cy - 70), (cx - 70, cy + 70)], fill=C_ACCENT, width=4)
    d.text((cx - 40, cy - 14), "карантин" if lang == "ru" else "quarantine",
           font=F_SMALL, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Изоляция / Isolation:", "зоны, объекты" if lang == "ru"
         else "zones, objects"),
        ("Фильтрация / Filtration:", "воздух, здоровье" if lang == "ru"
         else "air, health"),
        ("Протоколы / Protocols:", "вспышка заболевания" if lang == "ru"
         else "disease outbreak"),
    ], lang)
    save(img, RU_DIR / "fig19_epidemic.png", EN_DIR / "fig19_epidemic.png")


# ═════════════════════════════════════════════════════════════════════════════
# 20. Акустика
# ═════════════════════════════════════════════════════════════════════════════
def make_fig20(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Акустическая комфортность станции",
                   "Station acoustic comfort", lang)

    cx, cy = 340, 360
    # звуковые волны
    for i in range(5):
        rad = 40 + i * 20
        d.arc([cx - rad, cy - rad, cx + rad, cy + rad], start=0, end=180,
              fill=C_ACCENT, width=3)
    d.text((cx - 40, cy - 12), "45 дБ" if lang == "ru" else "45 dB",
           font=F_TITLE, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 200, [
        ("Шум / Noise:", "не более 45 дБ" if lang == "ru" else "not more than 45 dB"),
        ("Поглощение / Absorp.:", "покрытия, виброзащ." if lang == "ru"
         else "coatings, vibration isol."),
    ], lang)
    save(img, RU_DIR / "fig20_acoustics.png", EN_DIR / "fig20_acoustics.png")


# ═════════════════════════════════════════════════════════════════════════════
# 21. Летучие вещества
# ═════════════════════════════════════════════════════════════════════════════
def make_fig21(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Летучие вещества станции",
                   "Station volatiles", lang)

    molecules = [
        ("H₂O", (100, 180, 220)),
        ("NH₃", (120, 220, 120)),
        ("CH₄", (220, 180, 80)),
        ("CO₂", (220, 100, 100)),
    ]
    xx = 140
    for name, col in molecules:
        d.ellipse([xx - 30, 280, xx + 30, 340], fill=(*col, 60), outline=col, width=3)
        d.text((xx - 12, 300), name, font=F_PARAM_BOLD, fill=C_TEXT)
        xx += 110

    px = 540
    draw_panel(d, px, 110, W - px - 24, 200, [
        ("Вещества / Substances:", "вода, аммиак, метан, CO₂" if lang == "ru"
         else "water, ammonia, methane, CO₂"),
        ("Переработка / Recycling:", "циклы, повторное использов." if lang == "ru"
         else "cycles, reuse"),
    ], lang)
    save(img, RU_DIR / "fig21_volatiles.png", EN_DIR / "fig21_volatiles.png")


# ═════════════════════════════════════════════════════════════════════════════
# 22. Астероиды
# ═════════════════════════════════════════════════════════════════════════════
def make_fig22(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Добыча ресурсов с астероидов",
                   "Asteroid resource mining", lang)

    cx, cy = 340, 360
    # астероид (неправильная форма)
    d.polygon([(cx - 70, cy - 40), (cx - 20, cy - 70), (cx + 40, cy - 50),
               (cx + 70, cy - 10), (cx + 50, cy + 60), (cx - 40, cy + 40)],
              fill=(90, 90, 100), outline=C_CYL2, width=4)
    d.text((cx - 40, cy + 70), "6178 1986 DA", font=F_SMALL, fill=C_TEXT)
    # стрелка к станции
    d.line([(cx + 80, cy), (cx + 150, cy)], fill=C_ACCENT, width=4)
    d.polygon([(cx + 150, cy - 8), (cx + 160, cy), (cx + 150, cy + 8)],
              fill=C_ACCENT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 200, [
        ("Источник металла / Source:", "астероид 6178" if lang == "ru"
         else "asteroid 6178"),
        ("Добыча / Mining:", "автоматические работы" if lang == "ru"
         else "automated operations"),
    ], lang)
    save(img, RU_DIR / "fig22_asteroids.png", EN_DIR / "fig22_asteroids.png")


# ═════════════════════════════════════════════════════════════════════════════
# 23. Карантинная зона
# ═════════════════════════════════════════════════════════════════════════════
def make_fig23(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Карантинная зона станции",
                   "Station quarantine zone", lang)

    cx, cy = 340, 360
    d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90],
              fill=(*C_CYL1, 50), outline=C_CYL1, width=5)
    d.rectangle([cx - 30, cy - 90, cx + 30, cy + 90], fill=C_ACCENT)
    d.text((cx - 40, cy + 100), "защита экосистемы" if lang == "ru"
           else "ecosystem protection", font=F_SMALL, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Изоляция / Isolation:", "новые объекты, персонал" if lang == "ru"
         else "new objects, personnel"),
        ("Био-защита / Bio-prot.:", "экосистема станции" if lang == "ru"
         else "station ecosystem"),
    ], lang)
    save(img, RU_DIR / "fig23_quarantine.png", EN_DIR / "fig23_quarantine.png")


# ═════════════════════════════════════════════════════════════════════════════
# 24. Выбор радиаторной панели
# ═════════════════════════════════════════════════════════════════════════════
def make_fig24(lang: str) -> None:
    img = Image.new("RGB", (W, H), C_BG_BOT)
    gradient_bg(img)
    d = ImageDraw.Draw(img)
    y = draw_title(d, "Выбор панелей радиатора",
                   "Radiator panel selection", lang)

    cx, cy = 340, 360
    # радиаторные панели
    for i in range(4):
        yy = cy - 60 + i * 40
        d.rectangle([cx - 60, yy, cx + 60, yy + 28],
                    fill=(*C_ACCENT, 60), outline=C_ACCENT, width=3)
        d.text((cx + 70, yy + 4), f"панель {i+1}" if lang == "ru" else f"panel {i+1}",
               font=F_SMALL, fill=C_TEXT)

    px = 540
    draw_panel(d, px, 110, W - px - 24, 240, [
        ("Материалы / Materials:", "площадь, рама" if lang == "ru"
         else "area, frame"),
        ("Оптимизация / Opt.:", "теплоотвод, масса" if lang == "ru"
         else "heat rejection, mass"),
    ], lang)
    save(img, RU_DIR / "fig24_panel_choice.png", EN_DIR / "fig24_panel_choice.png")


MAKERS = {
    "fig01": make_fig01, "fig02": make_fig02, "fig03": make_fig03,
    "fig04": make_fig04, "fig05": make_fig05, "fig06": make_fig06,
    "fig07": make_fig07, "fig08": make_fig08, "fig09": make_fig09,
    "fig10": make_fig10, "fig11": make_fig11, "fig12": make_fig12,
    "fig13": make_fig13, "fig14": make_fig14, "fig15": make_fig15,
    "fig16": make_fig16, "fig17": make_fig17, "fig18": make_fig18,
    "fig19": make_fig19, "fig20": make_fig20, "fig21": make_fig21,
    "fig22": make_fig22, "fig23": make_fig23, "fig24": make_fig24,
}

if __name__ == "__main__":
    for key, make in MAKERS.items():
        if key == "fig01":
            make()
        else:
            make("ru")
            make("en")
    print("\nВсе 48 картинок сгенерировано.")
