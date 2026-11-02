#!/usr/bin/env python3
"""Генерация иллюстраций галереи ММОСО'Н на русском и английском.

Правильная конфигурация цилиндра (по docs/README.md):
  * Два встречно вращающихся цилиндра, радиус 5 000 м
  * Длина цилиндрической части 40 км (полная 49 км)
  * Угловая скорость 0,04429 рад/с (0,423 об/мин), тяжесть на ободе 1,0 g
  * Освещение только реакторное через осевые светотепловые балки
  * Зеркал и солнечного паруса у станции НЕТ
  * Масса станции 46,70 млрд т, население 1 000 000, мощность 721,4 ГВт
"""

from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RU_DIR = Path("site/assets/fig")
EN_DIR = Path("site/assets/fig_en")
RU_DIR.mkdir(parents=True, exist_ok=True)
EN_DIR.mkdir(parents=True, exist_ok=True)

# ═══ ШРИФТЫ ═══
try:
    F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    F_REG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    F_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except Exception:
    F_TITLE = ImageFont.load_default()
    F_REG = ImageFont.load_default()
    F_SMALL = ImageFont.load_default()

C_TEXT = (20, 20, 20, 255)
C_LABEL = (50, 50, 50, 255)
C_VALUE = (80, 80, 80, 255)
C_LINE = (120, 120, 120, 255)
C_CYL = (60, 90, 140, 255)
C_CYL2 = (140, 90, 60, 255)
C_AXIS = (200, 200, 200, 255)
C_BG = (255, 255, 255, 255)

W, H = 1600, 900


def new_canvas() -> Image.Image:
    return Image.new("RGBA", (W, H), C_BG)


def save(img: Image.Image, path: Path) -> None:
    img.convert("RGB").save(path, "PNG")
    print(f"  saved {path}")


def draw_title(draw: ImageDraw.Draw, x: int, y: int, text: str, font=F_TITLE) -> int:
    draw.text((x, y), text, font=font, fill=C_TEXT)
    return y + 50


def draw_param(draw: ImageDraw.Draw, x: int, y: int, label: str, value: str,
               font=F_REG, gap: int = 34) -> int:
    draw.text((x, y), label, font=font, fill=C_LABEL)
    draw.text((x + 520, y), value, font=font, fill=C_VALUE)
    return y + gap


def draw_cylinder_pair(draw: ImageDraw.Draw, cx: int, cy: int, r: int, length: int,
                       angle1: float, angle2: float) -> None:
    """Рисует два встречно вращающихся цилиндра соединяя их осью."""
    # Осевая балка по центру
    draw.line([(cx - length // 2, cy), (cx + length // 2, cy)], fill=C_AXIS, width=6)
    # Левый цилиндр
    draw.ellipse([cx - length // 2 - r, cy - r, cx - length // 2 + r, cy + r],
                 outline=C_CYL, width=4)
    draw.line([(cx - length // 2, cy - r), (cx - length // 2, cy + r)], fill=C_CYL, width=4)
    # Правый цилиндр
    draw.ellipse([cx + length // 2 - r, cy - r, cx + length // 2 + r, cy + r],
                 outline=C_CYL2, width=4)
    draw.line([(cx + length // 2, cy - r), (cx + length // 2, cy + r)], fill=C_CYL2, width=4)
    # Стрелки вращения (встречные)
    draw.arc([cx - length // 2 - r - 30, cy - r - 30, cx - length // 2 + r + 30, cy + r + 30],
             start=0, end=90, fill=C_CYL, width=4)
    draw.arc([cx + length // 2 - r - 30, cy - r - 30, cx + length // 2 + r + 30, cy + r + 30],
             start=180, end=270, fill=C_CYL2, width=4)


def zone_lines(lines: list[tuple[str, str]]) -> int:
    h = 0
    for _, v in lines:
        h += 32
    return h


# ═════════════════════════════════════════════════════════════════════════════
# 01. Компоновка станции
# ═════════════════════════════════════════════════════════════════════════════
def make_fig01(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Компоновка станции: два встречно вращающихся цилиндра")
        draw_cylinder_pair(d, 800, 450, 140, 600, 0, 0)
        y = 620
        y = draw_param(d, 60, y, "Радиус цилиндра:", "5 000 м")
        y = draw_param(d, 60, y, "Длина цилиндрической части:", "40 км (полная 49 км)")
        y = draw_param(d, 60, y, "Угловая скорость:", "0,04429 рад/с (0,423 об/мин)")
        y = draw_param(d, 60, y, "Тяжесть на ободе:", "1,0 g")
        y = draw_param(d, 60, y, "Число цилиндров:", "2, встречного вращения")
        y += 10
        d.text((60, y), "Освещение только реакторное через осевые", font=F_REG, fill=C_LABEL)
        d.text((60, y + 30), "светотепловые балки. Зеркал и солнечного паруса нет.", font=F_REG, fill=C_LABEL)
    else:
        y = draw_title(d, 60, 40, "Station layout: two counter-rotating cylinders")
        draw_cylinder_pair(d, 800, 450, 140, 600, 0, 0)
        y = 620
        y = draw_param(d, 60, y, "Cylinder radius:", "5 000 m")
        y = draw_param(d, 60, y, "Cylindrical part length:", "40 km (full 49 km)")
        y = draw_param(d, 60, y, "Angular velocity:", "0.04429 rad/s (0.423 rpm)")
        y = draw_param(d, 60, y, "Gravity at rim:", "1.0 g")
        y = draw_param(d, 60, y, "Number of cylinders:", "2, counter-rotating")
        y += 10
        d.text((60, y), "Lighting only reactor-driven via axial", font=F_REG, fill=C_LABEL)
        d.text((60, y + 30), "light-heat beams. No mirrors or solar sails.", font=F_REG, fill=C_LABEL)
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig01_layout.png")


# ═════════════════════════════════════════════════════════════════════════════
# 02. Разрез станции
# ═════════════════════════════════════════════════════════════════════════════
def make_fig02(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    r = 150
    # Поперечный разрез цилиндра
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=C_CYL, width=5)
    d.line([(cx - r, cy), (cx + r, cy)], fill=C_LINE, width=2)
    d.line([(cx, cy - r), (cx, cy + r)], fill=C_LINE, width=2)
    # Внутренняя оболочка
    d.ellipse([cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20], outline=C_CYL2, width=3)
    # Ось вращения
    d.line([(cx, cy - r), (cx, cy + r)], fill=C_AXIS, width=3)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Разрез станции: поперечный и продольный вид")
        y = draw_param(d, 60, y, "Оболочка:", "сталь 18Ni(300), пояс 850 мм")
        y = draw_param(d, 60, y, "Внутренние перегородки:", "климатические зоны вдоль радиуса")
        y = draw_param(d, 60, y, "Ось вращения:", "осевая светотепловая балка")
    else:
        y = draw_title(d, 60, 30, "Station section: cross-section and longitudinal view")
        y = draw_param(d, 60, y, "Envelope:", "steel 18Ni(300), belt 850 mm")
        y = draw_param(d, 60, y, "Internal partitions:", "climatic zones along radius")
        y = draw_param(d, 60, y, "Rotation axis:", "axial light-heat beam")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig02_section.png")


# ═════════════════════════════════════════════════════════════════════════════
# 03. Искусственная гравитация
# ═════════════════════════════════════════════════════════════════════════════
def make_fig03(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    r = 160
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=C_CYL, width=5)
    d.line([(cx, cy), (cx + r, cy)], fill=C_AXIS, width=4)
    d.text((cx + r + 10, cy - 10), "1,0 g", font=F_TITLE, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Искусственная гравитация станции")
        y = draw_param(d, 60, y, "Ускорение на поверхности цилиндра:", "1,0 g")
        y = draw_param(d, 60, y, "Радиус вращения:", "5 000 м")
        y = draw_param(d, 60, y, "Угловая скорость:", "0,04429 рад/с")
    else:
        y = draw_title(d, 60, 30, "Station artificial gravity")
        y = draw_param(d, 60, y, "Free-fall acceleration at surface:", "1.0 g")
        y = draw_param(d, 60, y, "Rotation radius:", "5 000 m")
        y = draw_param(d, 60, y, "Angular velocity:", "0.04429 rad/s")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig03_gravity.png")


# ═════════════════════════════════════════════════════════════════════════════
# 04. Климатические зоны
# ═════════════════════════════════════════════════════════════════════════════
def make_fig04(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 700, 450
    zones = [
        (0, 10, "тropical / тропическая", C_CYL),
        (10, 22, "subtropical / субтропическая", (200, 140, 60)),
        (22, 32, "moderate / умеренная", (100, 160, 80)),
        (32, 40, "cold / холодная", (120, 140, 180)),
    ]
    y0 = 200
    for i, (km0, km1, name, col) in enumerate(zones):
        h = 60
        d.rectangle([cx - 180, y0 + i * (h + 10), cx + 180, y0 + i * (h + 10) + h], fill=(*col[:3], 60), outline=col, width=3)
        d.text((cx - 170, y0 + i * (h + 10) + 15), f"{km0}–{km1} км", font=F_REG, fill=C_TEXT)
        d.text((cx - 60, y0 + i * (h + 10) + 15), name, font=F_REG, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Климатические зоны цилиндра")
        d.text((60, y), "Климатические зоны, км от переднего торца:", font=F_REG, fill=C_LABEL)
        y += 40
        zones_ru = [
            ("тропическая", "0–10", "+28 … +35 °С, влажность 70–85 %"),
            ("субтропическая", "10–22", "+15 … +28 °С, влажность 60–70 %"),
            ("умеренная", "22–32", "+0 … +15 °С, влажность 55–65 %"),
            ("холодная", "32–40", "-15 … -5 °С, влажность 40–50 %"),
        ]
        for name, km, temp in zones_ru:
            draw_param(d, 60, y, f"{name}, {km} км:", temp)
    else:
        y = draw_title(d, 60, 30, "Climatic zones of the cylinder")
        d.text((60, y), "Climatic zones, km from cylinder end:", font=F_REG, fill=C_LABEL)
        y += 40
        zones_en = [
            ("Tropical", "0–10", "+28…+35 °C · humidity 70–85 %"),
            ("Subtropical", "10–22", "+15…+28 °C · humidity 60–70 %"),
            ("Moderate", "22–32", "+0…+15 °C · humidity 55–65 %"),
            ("Cold", "32–40", "-15…-5 °C · humidity 40–50 %"),
        ]
        for name, km, temp in zones_en:
            draw_param(d, 60, y, f"{name}, {km} km:", temp)
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig04_climate.png")


# ═════════════════════════════════════════════════════════════════════════════
# 05. Давление
# ═════════════════════════════════════════════════════════════════════════════
def make_fig05(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], outline=C_CYL, width=5)
    d.text((cx - 40, cy - 15), "101,3 кПа / 101.3 kPa", font=F_TITLE, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Атмосферное давление станции")
        y = draw_param(d, 60, y, "Давление на уровне моря:", "101,3 кПа")
        y = draw_param(d, 60, y, "Состав воздуха:", "N₂ 78 %, O₂ 21 %, остальные 1 %")
        y = draw_param(d, 60, y, "Избыточное давление в оболочке:", "не более 5 кПа")
    else:
        y = draw_title(d, 60, 30, "Station atmospheric pressure")
        y = draw_param(d, 60, y, "Pressure at sea level:", "101.3 kPa")
        y = draw_param(d, 60, y, "Air composition:", "N₂ 78 % · O₂ 21 % · others 1 %")
        y = draw_param(d, 60, y, "Excess pressure in envelope:", "not more than 5 kPa")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig05_pressure.png")


# ═════════════════════════════════════════════════════════════════════════════
# 06. Сталь
# ═════════════════════════════════════════════════════════════════════════════
def make_fig06(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Структурная сталь 18Ni(300)")
        y = draw_param(d, 60, y, "Прочность на растяжение:", "1 200 МПа")
        y = draw_param(d, 60, y, "Плотность:", "7 850 кг/м³")
        y = draw_param(d, 60, y, "Пояс оболочки:", "850 мм")
        y = draw_param(d, 60, y, "Источник металла:", "астероид 6178 1986 DA")
    else:
        y = draw_title(d, 60, 40, "Structural steel 18Ni(300)")
        y = draw_param(d, 60, y, "Tensile strength:", "1 200 MPa")
        y = draw_param(d, 60, y, "Density:", "7 850 kg/m³")
        y = draw_param(d, 60, y, "Envelope belt:", "850 mm")
        y = draw_param(d, 60, y, "Metal source:", "asteroid 6178 1986 DA")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig06_steel.png")


# ═════════════════════════════════════════════════════════════════════════════
# 07. Нагрузки
# ═════════════════════════════════════════════════════════════════════════════
def make_fig07(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Динамические нагрузки на конструкции станции")
        y = draw_param(d, 60, y, "Вращающиеся цилиндры:", "центробежные нагрузки")
        y = draw_param(d, 60, y, "Неподвижная рама:", "статические нагрузки от причалов")
        y = draw_param(d, 60, y, "Макс. нагрузка на опорный узел:", "не превышает проектную")
    else:
        y = draw_title(d, 60, 40, "Dynamic loads on station structures")
        y = draw_param(d, 60, y, "Rotating cylinders:", "centrifugal loads")
        y = draw_param(d, 60, y, "Non-rotating frame:", "static loads from docks")
        y = draw_param(d, 60, y, "Max load on support node:", "within design limit")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig07_load.png")


# ═════════════════════════════════════════════════════════════════════════════
# 08. Масса
# ═════════════════════════════════════════════════════════════════════════════
def make_fig08(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Масса станции по элементам")
        y = draw_param(d, 60, y, "Общая масса станции:", "не более 46,70 млрд тонн")
        y = draw_param(d, 60, y, "Доля конструкционных материалов:", "94 %")
        y = draw_param(d, 60, y, "Доля жизнеобеспечения:", "3,5 %")
        y = draw_param(d, 60, y, "Доля оборудования и приборов:", "2,5 %")
    else:
        y = draw_title(d, 60, 40, "Station mass by elements")
        y = draw_param(d, 60, y, "Total station mass:", "not more than 46.70 billion tonnes")
        y = draw_param(d, 60, y, "Share of structural materials:", "94 %")
        y = draw_param(d, 60, y, "Share of life support:", "3.5 %")
        y = draw_param(d, 60, y, "Share of equipment and instruments:", "2.5 %")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig08_mass.png")


# ═════════════════════════════════════════════════════════════════════════════
# 09. Тепловой баланс
# ═════════════════════════════════════════════════════════════════════════════
def make_fig09(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Тепловой баланс станции")
        y = draw_param(d, 60, y, "Источники тепла:", "реакторы, оборудование, люди")
        y = draw_param(d, 60, y, "Отвод тепла:", "радиаторные панели на раме")
        y = draw_param(d, 60, y, "Теплообмен между цилиндрами:", "не происходит (ось соединения)")
    else:
        y = draw_title(d, 60, 40, "Station thermal balance")
        y = draw_param(d, 60, y, "Heat sources:", "reactors, equipment, people")
        y = draw_param(d, 60, y, "Heat rejection:", "radiator panels on frame")
        y = draw_param(d, 60, y, "Heat exchange between cylinders:", "does not occur (axis link)")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig09_thermal.png")


# ═════════════════════════════════════════════════════════════════════════════
# 10. Энергетика
# ═════════════════════════════════════════════════════════════════════════════
def make_fig10(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Баланс энергии станции")
        y = draw_param(d, 60, y, "Источники:", "ядерные реакторы (реакторное освещение)")
        y = draw_param(d, 60, y, "Электрическая мощность:", "721,4 ГВт")
        y = draw_param(d, 60, y, "Распределение:", "жизнеобеспечение, производство, климат")
    else:
        y = draw_title(d, 60, 40, "Station energy balance")
        y = draw_param(d, 60, y, "Sources:", "nuclear reactors (reactor lighting)")
        y = draw_param(d, 60, y, "Electric power:", "721.4 GW")
        y = draw_param(d, 60, y, "Distribution:", "life support, production, climate")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig10_energy.png")


# ═════════════════════════════════════════════════════════════════════════════
# 11. Стыковка
# ═════════════════════════════════════════════════════════════════════════════
def make_fig11(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.rectangle([cx - 150, cy - 60, cx + 150, cy + 60], outline=C_CYL, width=4)
    d.line([(cx, cy - 60), (cx, cy + 60)], fill=C_AXIS, width=3)
    d.text((cx - 70, cy - 20), "причал / dock", font=F_SMALL, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Система стыковки станции")
        y = draw_param(d, 60, y, "Причалы:", "на вращающемся цилиндре и раме")
        y = draw_param(d, 60, y, "Переход:", "через ось между сегментами")
    else:
        y = draw_title(d, 60, 30, "Station docking system")
        y = draw_param(d, 60, y, "Docks:", "on rotating cylinder and frame")
        y = draw_param(d, 60, y, "Transition:", "through axis between segments")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig11_docking.png")


# ═════════════════════════════════════════════════════════════════════════════
# 12. Кориолис
# ═════════════════════════════════════════════════════════════════════════════
def make_fig12(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.ellipse([cx - 140, cy - 140, cx + 140, cy + 140], outline=C_CYL, width=4)
    d.line([(cx, cy - 30), (cx + 100, cy + 60)], fill=C_LINE, width=3)
    d.text((cx + 105, cy + 65), "Coriolis / Кориолис", font=F_SMALL, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Силы Кориолиса на станции")
        y = draw_param(d, 60, y, "Угловая скорость цилиндра:", "0,04429 рад/с")
        y = draw_param(d, 60, y, "Отклонение:", "при радиальном перемещении")
        y = draw_param(d, 60, y, "Компенсация:", "навигация и управление")
    else:
        y = draw_title(d, 60, 40, "Coriolis forces on station")
        y = draw_param(d, 60, y, "Cylinder angular rotation:", "0.04429 rad/s")
        y = draw_param(d, 60, y, "Deflection:", "during radial movement")
        y = draw_param(d, 60, y, "Compensation:", "navigation and control")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig12_coriolis.png")


# ═════════════════════════════════════════════════════════════════════════════
# 13. Подъем по радиусу
# ═════════════════════════════════════════════════════════════════════════════
def make_fig13(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], outline=C_CYL, width=4)
    d.line([(cx, cy), (cx, cy - 150)], fill=C_LINE, width=3)
    d.text((cx + 20, cy - 100), "0 g → 1 g", font=F_REG, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Подъем по радиусу цилиндра")
        y = draw_param(d, 60, y, "Воспринимаемая гравитация:", "меняется с радиусом")
        y = draw_param(d, 60, y, "От центра к поверхности:", "от 0 g до 1 g")
        y = draw_param(d, 60, y, "Ограничения:", "для тяжелой техники")
    else:
        y = draw_title(d, 60, 40, "Climb along cylinder radius")
        y = draw_param(d, 60, y, "Perceived gravity:", "changes with radius")
        y = draw_param(d, 60, y, "Center to surface:", "from 0 g to 1 g")
        y = draw_param(d, 60, y, "Restrictions:", "for heavy equipment")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig13_climb.png")


# ═════════════════════════════════════════════════════════════════════════════
# 14. Падение
# ═════════════════════════════════════════════════════════════════════════════
def make_fig14(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.ellipse([cx - 140, cy - 140, cx + 140, cy + 140], outline=C_CYL, width=4)
    d.line([(cx - 60, cy - 60), (cx + 60, cy + 60)], fill=C_LINE, width=3)
    d.text((cx + 70, cy + 70), "траектория / trajectory", font=F_SMALL, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Падение на станции")
        y = draw_param(d, 60, y, "Траектория:", "во вращающемся фрейме")
        y = draw_param(d, 60, y, "Сила Кориолиса:", "влияние на траекторию")
        y = draw_param(d, 60, y, "Безопасность:", "перемещения внутри цилиндра")
    else:
        y = draw_title(d, 60, 40, "Fall on station")
        y = draw_param(d, 60, y, "Trajectory:", "in rotating frame")
        y = draw_param(d, 60, y, "Coriolis force effect:", "on trajectory")
        y = draw_param(d, 60, y, "Safety:", "of movement inside cylinder")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig14_fall.png")


# ═════════════════════════════════════════════════════════════════════════════
# 15. Транспортный маршрут
# ═════════════════════════════════════════════════════════════════════════════
def make_fig15(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Маршрут от дока к обитаемой поверхности")
        steps = [
            ("1", "Кабельная оболочка к неподвижной раме"),
            ("2", "Опорный узел: переход к вращению"),
            ("3", "Тепловой барьер от контура ОСС"),
            ("4", "Корпус внутри тороидальной оболочки"),
            ("5", "Осевая светотепловая балка"),
            ("6", "Слой гравитации 1 000 г"),
            ("7", "Производственная зона, закрыта для людей"),
        ]
    else:
        y = draw_title(d, 60, 40, "Route from dock to habitable surface")
        steps = [
            ("1", "Cable fairing to non-rotating frame"),
            ("2", "Support node: transition to rotation"),
            ("3", "Thermal barrier from OSC circuit"),
            ("4", "Hull inside toroidal envelope"),
            ("5", "Axial light-heat beam"),
            ("6", "Gravity layer 1 000 g"),
            ("7", "Production zone, closed for people"),
        ]
    for num, txt in steps:
        d.text((60, y), f"{num}. {txt}", font=F_REG, fill=C_TEXT)
        y += 34
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig15_transport.png")


# ═════════════════════════════════════════════════════════════════════════════
# 16. Ресурсы
# ═════════════════════════════════════════════════════════════════════════════
def make_fig16(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Потребность в материалах: 46,70 млрд тонн")
        items = [
            ("1", "Сталь 18Ni(300), конструкции", "астероид 6178 1986 DA"),
            ("2", "Реголит, структура", "переработка, общий"),
            ("3", "Дышащая смесь (N₂, O₂)", "концепт гл. 8"),
            ("4", "Реголит, борид карбида", "рыхлый реголит"),
            ("5", "Вода", "концепт гл. 8"),
            ("6", "Оболочка, теплоизоляция", "общий"),
        ]
    else:
        y = draw_title(d, 60, 40, "Material requirement: 46.70 billion tonnes")
        items = [
            ("1", "Steel 18Ni(300), structures", "asteroid 6178 1986 DA"),
            ("2", "Regolith, structure", "reprocessing, general"),
            ("3", "Breathable mix (N2, O2)", "concept ch. 8"),
            ("4", "Regolith, boron carbide", "loose regolith"),
            ("5", "Water", "concept ch. 8"),
            ("6", "Shell, thermal insulation", "general"),
        ]
    for num, txt, sub in items:
        d.text((60, y), f"{num}. {txt}", font=F_REG, fill=C_TEXT)
        d.text((300, y), f"— {sub}", font=F_SMALL, fill=C_LABEL)
        y += 38
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig16_resources.png")


# ═════════════════════════════════════════════════════════════════════════════
# 17. Питание
# ═════════════════════════════════════════════════════════════════════════════
def make_fig17(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Система питания станции")
        y = draw_param(d, 60, y, "Сельскохозяйственные зоны:", "растения, грибы, микрозелень")
        y = draw_param(d, 60, y, "Рыбоводство:", "пруды на стационарных платформах")
        y = draw_param(d, 60, y, "Производственные циклы:", "переработка биомассы")
    else:
        y = draw_title(d, 60, 40, "Station food system")
        y = draw_param(d, 60, y, "Agricultural zones:", "plants, fungi, microgreens")
        y = draw_param(d, 60, y, "Aquaculture:", "ponds on fixed platforms")
        y = draw_param(d, 60, y, "Production cycles:", "biomass processing")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig17_food.png")


# ═════════════════════════════════════════════════════════════════════════════
# 18. Использование земли
# ═════════════════════════════════════════════════════════════════════════════
def make_fig18(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Использование земли двух цилиндров")
        y = draw_param(d, 60, y, "Биосфера:", "1 550,1 км² на цилиндр")
        y = draw_param(d, 60, y, "Посевные площади:", "807 км² · 54 % · 14 культур")
        y = draw_param(d, 60, y, "Свободный резерв:", "536 км² · 36 %")
        y = draw_param(d, 60, y, "Рыбные пруды:", "15 км² · 1 %")
    else:
        y = draw_title(d, 60, 40, "Land use of two cylinders")
        y = draw_param(d, 60, y, "Biosphere:", "1 550.1 km² per cylinder")
        y = draw_param(d, 60, y, "Sowing areas:", "807 km² · 54 % · 14 crops")
        y = draw_param(d, 60, y, "Free reserve:", "536 km² · 36 %")
        y = draw_param(d, 60, y, "Fish ponds:", "15 km² · 1 %")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig18_land.png")


# ═════════════════════════════════════════════════════════════════════════════
# 19. Эпидемия / Карантин
# ═════════════════════════════════════════════════════════════════════════════
def make_fig19(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Система карантина и эпидемиологической безопасности")
        y = draw_param(d, 60, y, "Изоляция:", "больных зон и новых объектов")
        y = draw_param(d, 60, y, "Фильтрация:", "воздуха и мониторинг здоровья")
        y = draw_param(d, 60, y, "Протоколы:", "при вспышке заболевания")
    else:
        y = draw_title(d, 60, 40, "Station quarantine and epidemiological safety")
        y = draw_param(d, 60, y, "Isolation:", "sick zones and new objects")
        y = draw_param(d, 60, y, "Filtration:", "air and health monitoring")
        y = draw_param(d, 60, y, "Protocols:", "during disease outbreak")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig19_epidemic.png")


# ═════════════════════════════════════════════════════════════════════════════
# 20. Акустика
# ═════════════════════════════════════════════════════════════════════════════
def make_fig20(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Акустическая комфортность станции")
        y = draw_param(d, 60, y, "Уровень шума в жилых зонах:", "не более 45 дБ")
        y = draw_param(d, 60, y, "Звукопоглощение:", "покрытия и виброзащита")
    else:
        y = draw_title(d, 60, 40, "Station acoustic comfort")
        y = draw_param(d, 60, y, "Noise level in living zones:", "not more than 45 dB")
        y = draw_param(d, 60, y, "Sound absorption:", "coatings and vibration isolation")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig20_acoustics.png")


# ═════════════════════════════════════════════════════════════════════════════
# 21. Летучие вещества
# ═════════════════════════════════════════════════════════════════════════════
def make_fig21(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Летучие вещества станции")
        y = draw_param(d, 60, y, "Вода, аммиак, метан, CO₂:", "источники и циклы")
        y = draw_param(d, 60, y, "Переработка:", "и повторное использование")
    else:
        y = draw_title(d, 60, 40, "Station volatiles")
        y = draw_param(d, 60, y, "Water, ammonia, methane, CO₂:", "sources and cycles")
        y = draw_param(d, 60, y, "Recycling:", "and reuse")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig21_volatiles.png")


# ═════════════════════════════════════════════════════════════════════════════
# 22. Астероиды
# ═════════════════════════════════════════════════════════════════════════════
def make_fig22(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = 800, 450
    d.ellipse([cx - 90, cy - 50, cx + 90, cy + 50], outline=C_CYL, width=4)
    d.text((cx - 30, cy - 12), "6178 1986 DA", font=F_SMALL, fill=C_TEXT)
    d.line([(cx + 100, cy), (cx + 200, cy)], fill=C_LINE, width=3)
    d.text((cx + 210, cy - 12), "доставка на станцию", font=F_SMALL, fill=C_TEXT)
    if lang == "ru":
        y = draw_title(d, 60, 30, "Добыча ресурсов с астероидов")
        y = draw_param(d, 60, y, "Основной источник металла:", "астероид 6178 1986 DA")
        y = draw_param(d, 60, y, "Добыча:", "автоматические горные работы")
    else:
        y = draw_title(d, 60, 30, "Asteroid resource mining")
        y = draw_param(d, 60, y, "Main metal source:", "asteroid 6178 1986 DA")
        y = draw_param(d, 60, y, "Mining:", "automated operations")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig22_asteroids.png")


# ═════════════════════════════════════════════════════════════════════════════
# 23. Карантинная зона
# ═════════════════════════════════════════════════════════════════════════════
def make_fig23(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Карантинная зона станции")
        y = draw_param(d, 60, y, "Изоляция:", "новых объектов и персонала")
        y = draw_param(d, 60, y, "Биологическая защита:", "экосистемы станции")
    else:
        y = draw_title(d, 60, 40, "Station quarantine zone")
        y = draw_param(d, 60, y, "Isolation:", "new objects and personnel")
        y = draw_param(d, 60, y, "Biological protection:", "of station ecosystem")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig23_quarantine.png")


# ═════════════════════════════════════════════════════════════════════════════
# 24. Выбор радиаторной панели
# ═════════════════════════════════════════════════════════════════════════════
def make_fig24(lang: str) -> None:
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if lang == "ru":
        y = draw_title(d, 60, 40, "Выбор панелей радиатора")
        y = draw_param(d, 60, y, "Материалы:", "площадь и расположение на раме")
        y = draw_param(d, 60, y, "Оптимизация:", "теплоотвода и массы")
    else:
        y = draw_title(d, 60, 40, "Radiator panel selection")
        y = draw_param(d, 60, y, "Materials:", "area and placement on frame")
        y = draw_param(d, 60, y, "Optimization:", "heat rejection and mass")
    save(img, (RU_DIR if lang == "ru" else EN_DIR) / "fig24_panel_choice.png")


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
        for lang in ("ru", "en"):
            make(lang)
    print("\nВсе 48 картинок сгенерировано.")
