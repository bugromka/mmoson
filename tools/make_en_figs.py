#!/usr/bin/env python3
"""Наложение английских подписей на чистые версии картинок галереи.

Сохраняет графику неизменной, добавляя английскую текстовую панель справа.
Картинки, где английский текст уже присутствует (fig02, fig10, fig17),
копируются как есть.

Текст располагается на тех же позициях, что и русский текст в оригинальных
картинках: справа от диаграммы, в одной текстовой колонке.
"""

from __future__ import annotations

import shutil
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

SRC = Path("site/assets/fig")
DST = Path("site/assets/fig_en")
DST.mkdir(exist_ok=True)

try:
    FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    FONT_REG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    FONT_WARN = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except Exception:
    FONT_TITLE = ImageFont.load_default()
    FONT_REG = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()
    FONT_WARN = ImageFont.load_default()

# Ширина текстовой панели справа — достаточно для длинных английских строк
PANEL_W = 950


def wrap_text(text: str, font, max_width: int) -> list[str]:
    """Переносит строку по словам, чтобы она не выходила за max_width."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for w in words[1:]:
        test = current + " " + w
        if font.getlength(test) <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


def add_panel(img: Image.Image, title: str, lines: list[tuple[str, str | None]],
              warn_lines: list[str] | None = None) -> Image.Image:
    """Добавляет текстовую панель шириной PANEL_W справа."""
    w, h = img.size
    canvas = Image.new("RGBA", (w + PANEL_W, h), (255, 255, 255, 255))
    canvas.paste(img, (0, 0))
    draw = ImageDraw.Draw(canvas)

    x = w + 30
    y = 30
    text_max_w = PANEL_W - 60  # отступы по краям панели

    # Заголовок
    draw.text((x, y), title, font=FONT_TITLE, fill=(20, 20, 20, 255))
    y += 50

    for label, value in lines:
        if label is None and value is None:
            y += 14
            continue

        # Рисуем метку (левая часть строки)
        if label:
            draw.text((x, y), label, font=FONT_REG, fill=(50, 50, 50, 255))

        # Рисуем значение (правая часть, с переносом если нужно)
        if value:
            label_w = FONT_REG.getlength(label) if label else 0
            value_x = x + 340
            avail_w = text_max_w - 340
            if FONT_REG.getlength(value) <= avail_w:
                draw.text((value_x, y), value, font=FONT_REG, fill=(80, 80, 80, 255))
                y += 38
            else:
                y += 38
                for sub in wrap_text(value, FONT_REG, text_max_w):
                    draw.text((x, y), sub, font=FONT_REG, fill=(80, 80, 80, 255))
                    y += 34
        else:
            y += 38

    if warn_lines:
        y += 16
        for wl in warn_lines:
            for sub in wrap_text(wl, FONT_WARN, text_max_w):
                draw.text((x, y), sub, font=FONT_WARN, fill=(180, 40, 40, 255))
                y += 32

    return canvas


def make_fig01() -> None:
    img = Image.open(SRC / "fig01_layout.png").convert("RGBA")
    out = add_panel(
        img,
        "Station layout: two counter-rotating cylinders",
        [
            ("Angular velocity", "0.05 π/s"),
            (None, None),
            ("1", "Support node — rotating cylinder shell"),
            ("", "and non-rotating frame"),
            ("2", "Non-rotating fairing frame —"),
            ("", "only rotation axis, no engines,"),
            ("", "cargo, reactors"),
            ("3", "Central solar mirror — indicates"),
            ("", "solar line: diameter 8 m at"),
            ("", "cylinder diameter 10 km"),
            ("4", "Heat capacity — climatic zones,"),
            ("", "1 000 g"),
            ("5", "Radiator panels — mounted on"),
            ("", "frame, 1 477 km²"),
            (None, None),
            ("Climatic zones", "km from cylinder end"),
            ("tropical", "0–10"),
            ("subtropical", "10–22"),
            ("moderate", "22–32"),
            ("cold", "32–40"),
            (None, None),
        ],
        warn_lines=[
            "Heat exchange between cylinders",
            "does not occur: they rotate,",
            "and rigid connection by rim is",
            "impossible. Connection only",
            "through axis.",
        ],
    )
    out.save(DST / "fig01_layout.png")


def make_fig02() -> None:
    """fig02_section уже на английском — копируем как есть"""
    shutil.copy2(SRC / "fig02_section.png", DST / "fig02_section.png")


def make_fig03() -> None:
    img = Image.open(SRC / "fig03_gravity.png").convert("RGBA")
    out = add_panel(
        img,
        "Artificial gravity on station",
        [
            ("Gravity at cylinder surface", "1 g"),
            ("Rotation radius", "5 000 m"),
            ("Angular velocity", "0.05 π/s"),
        ],
    )
    out.save(DST / "fig03_gravity.png")


def make_fig04() -> None:
    img = Image.open(SRC / "fig04_climate.png").convert("RGBA")
    out = add_panel(
        img,
        "Climatic zones of the cylinder",
        [
            ("1", "Tropical, 0–10 km"),
            ("", "+28...+35 °C · humidity 70–85 % ·"),
            ("", "solar 220 Wt/m²"),
            ("", "thermophilic cultures, rice,"),
            ("", "batat, bananas"),
            ("2", "Subtropical, 10–22 km"),
            ("", "+15...+28 °C · humidity 60–70 % ·"),
            ("", "solar 170 Wt/m²"),
            ("", "grains, soy, oilseeds, beets,"),
            ("", "arctic greens"),
            ("3", "Moderate, 22–32 km"),
            ("", "+0...+15 °C · humidity 55–65 % ·"),
            ("", "solar 120 Wt/m²"),
            ("", "spinach, cauliflower, chicory,"),
            ("", "oats, arctic grains"),
            ("4", "Cold, 32–40 km"),
            ("", "-15...-5 °C · humidity 40–50 % ·"),
            ("", "solar 60 Wt/m²"),
            ("", "only frost-resistant"),
            ("", "microgreens, no heating"),
        ],
    )
    out.save(DST / "fig04_climate.png")


def make_fig05() -> None:
    img = Image.open(SRC / "fig05_pressure.png").convert("RGBA")
    out = add_panel(
        img,
        "Station atmospheric pressure",
        [
            ("Pressure at sea level", "101.3 kPa"),
            ("Air composition", "N₂ 78 % · O₂ 21 % · others 1 %"),
            ("Excess pressure in envelope", "not more than 5 kPa"),
        ],
    )
    out.save(DST / "fig05_pressure.png")


def make_fig06() -> None:
    img = Image.open(SRC / "fig06_steel.png").convert("RGBA")
    out = add_panel(
        img,
        "Structural steel 18Ni(300)",
        [
            ("Tensile strength", "1 200 MPa"),
            ("Density", "7 850 kg/m³"),
            ("Total quantity", "20.83 billion tonnes"),
            ("Share of asteroid 6178 1986 DA", "94 %"),
        ],
    )
    out.save(DST / "fig06_steel.png")


def make_fig07() -> None:
    img = Image.open(SRC / "fig07_load.png").convert("RGBA")
    out = add_panel(
        img,
        "Dynamic loads on station structures",
        [
            ("Rotating cylinders", "centrifugal loads"),
            ("Non-rotating frame", "static loads from docks and equipment"),
            ("Max load on support node", "does not exceed design limit"),
        ],
    )
    out.save(DST / "fig07_load.png")


def make_fig08() -> None:
    img = Image.open(SRC / "fig08_mass.png").convert("RGBA")
    out = add_panel(
        img,
        "Station mass by elements",
        [
            ("Total station mass", "not more than 43.55 billion tonnes"),
            ("Share of structural materials", "94 %"),
            ("Share of life support", "3.5 %"),
            ("Share of equipment and instruments", "2.5 %"),
        ],
    )
    out.save(DST / "fig08_mass.png")


def make_fig09() -> None:
    img = Image.open(SRC / "fig09_thermal.png").convert("RGBA")
    out = add_panel(
        img,
        "Station thermal balance",
        [
            ("Heat sources", "solar radiation, equipment, people"),
            ("Heat rejection", "radiator panels 1 477 km²"),
            ("Heat exchange between cylinders", "does not occur"),
        ],
    )
    out.save(DST / "fig09_thermal.png")


def make_fig10() -> None:
    """fig10_energy уже содержит английский текст — копируем как есть"""
    shutil.copy2(SRC / "fig10_energy.png", DST / "fig10_energy.png")


def make_fig11() -> None:
    img = Image.open(SRC / "fig11_docking.png").convert("RGBA")
    out = add_panel(
        img,
        "Station docking system",
        [
            ("Docks", "on rotating cylinder and non-rotating frame"),
            ("Transition", "between rotating and non-rotating segments through axis"),
        ],
    )
    out.save(DST / "fig11_docking.png")


def make_fig12() -> None:
    img = Image.open(SRC / "fig12_coriolis.png").convert("RGBA")
    out = add_panel(
        img,
        "Coriolis forces on station",
        [
            ("Cylinder angular rotation", "0.05 π/s"),
            ("Deflection", "of moving objects during radial movement"),
            ("Compensation", "in navigation and control systems"),
        ],
    )
    out.save(DST / "fig12_coriolis.png")


def make_fig13() -> None:
    img = Image.open(SRC / "fig13_climb.png").convert("RGBA")
    out = add_panel(
        img,
        "Climb along cylinder radius",
        [
            ("Perceived gravity", "changes with radius"),
            ("Transition from center to surface", "from 0 g to 1 g"),
            ("Restrictions", "for heavy equipment"),
        ],
    )
    out.save(DST / "fig13_climb.png")


def make_fig14() -> None:
    img = Image.open(SRC / "fig14_fall.png").convert("RGBA")
    out = add_panel(
        img,
        "Fall on station",
        [
            ("Trajectory", "of falling object in rotating frame"),
            ("Coriolis force effect", "on trajectory"),
            ("Safety", "of movement inside cylinder"),
        ],
    )
    out.save(DST / "fig14_fall.png")


def make_fig15() -> None:
    img = Image.open(SRC / "fig15_transport.png").convert("RGBA")
    out = add_panel(
        img,
        "Route from dock to habitable surface",
        [
            ("1", "Cable fairing to non-rotating frame"),
            ("2", "Support node: transition to rotation"),
            ("3", "Thermal barrier separates fairing"),
            ("", "from OSC envelope"),
            ("4", "Hull placed inside toroidal fairing"),
            ("5", "Central solar mirror"),
            ("6", "Gravity layer 1 000 g"),
            ("7", "Production zone g < 2 500 m,"),
            ("", "closed for people"),
        ],
        warn_lines=[
            "Production volume radius up to 2 500 m closed",
            "for people: flux from OSC increases 300 W/m²,",
            "and beyond 500 m — 1 500 W/m². Mirror",
            "shielding leads to distantly controlled",
            "mechanisms. Free path along axis is reduced.",
        ],
    )
    out.save(DST / "fig15_transport.png")


def make_fig16() -> None:
    img = Image.open(SRC / "fig16_resources.png").convert("RGBA")
    out = add_panel(
        img,
        "Material requirement: total 43.55 billion tonnes",
        [
            ("1", "Steel 18Ni(300), structural fabric"),
            ("", "20.83 billion tonnes · resource share:"),
            ("", "94 % of asteroid metal (6178)"),
            ("", "1986 DA"),
            ("2", "Structural regolith"),
            ("", "8.13 billion tonnes · regolith"),
            ("", "reprocessing, general"),
            ("3", "Breathable mix (N2, O2)"),
            ("", "7.55 billion tonnes · conceptual"),
            ("", "program ch. 8; graphics,"),
            ("", "qualification and testing —"),
            ("", "in development"),
            ("4", "Regolith, boron carbide"),
            ("", "4.65 billion tonnes · loose"),
            ("", "regolith, general"),
            ("5", "Water"),
            ("", "1.17 billion tonnes · conceptual"),
            ("", "program ch. 8; graphics,"),
            ("", "qualification and testing —"),
            ("", "in development"),
            ("6", "Nickel-steel shell, thermal"),
            ("", "insulation 1.22 billion tonnes ·"),
            ("", "general"),
        ],
    )
    out.save(DST / "fig16_resources.png")


def make_fig17() -> None:
    """fig17_food уже содержит английский текст — копируем как есть"""
    shutil.copy2(SRC / "fig17_food.png", DST / "fig17_food.png")


def make_fig18() -> None:
    img = Image.open(SRC / "fig18_land.png").convert("RGBA")
    out = add_panel(
        img,
        "Land use of two cylinders, biosphere 1 508 km²",
        [
            ("1", "Sowing areas"),
            ("", "807 km² · 54 % · 14 crops,"),
            ("", "table 5.5; net 1.870"),
            ("", "trillion kcal"),
            ("2", "Free reserve"),
            ("", "536 km² · 36 % · including"),
            ("", "29.6 km² arctic crop"),
            ("", "strains"),
            ("3", "Reserve for variational"),
            ("", "cultures 150 km² · 10 % ·"),
            ("", "introduced after crop"),
            ("", "failure, not sown"),
            ("4", "Fish ponds"),
            ("", "15 km² · 1 % · natural feed,"),
            ("", "depth up to 3 m, p. B.11"),
        ],
    )
    draw = ImageDraw.Draw(out)
    w, h = out.size
    x = w - PANEL_W + 30
    y = 330
    footer = [
        "Biosphere accounts for 49 % of total",
        "area of 3 100.2 km²; remaining —",
        "buildings, roads, waterways",
        "150 km² of 1.2 m deep ponds",
        "and slopes. No heating in cold",
        "zone (p. B.12)",
    ]
    for fl in footer:
        draw.text((x, y), fl, font=FONT_REG, fill=(50, 50, 50, 255))
        y += 36
    out.save(DST / "fig18_land.png")


def make_fig19() -> None:
    img = Image.open(SRC / "fig19_epidemic.png").convert("RGBA")
    out = add_panel(
        img,
        "Station quarantine and epidemiological safety system",
        [
            ("Isolation", "of sick zones"),
            ("Air filtration", "and health monitoring"),
            ("Action protocols", "during disease outbreak"),
        ],
    )
    out.save(DST / "fig19_epidemic.png")


def make_fig20() -> None:
    img = Image.open(SRC / "fig20_acoustics.png").convert("RGBA")
    out = add_panel(
        img,
        "Station acoustic comfort",
        [
            ("Noise level in living zones", "not more than 45 dB"),
            ("Sound-absorbing coatings", "and vibration isolation"),
        ],
    )
    out.save(DST / "fig20_acoustics.png")


def make_fig21() -> None:
    img = Image.open(SRC / "fig21_volatiles.png").convert("RGBA")
    out = add_panel(
        img,
        "Station volatiles",
        [
            ("Water, ammonia, methane, carbon dioxide", "— sources and cycles"),
            ("Recycling", "and reuse"),
        ],
    )
    out.save(DST / "fig21_volatiles.png")


def make_fig22() -> None:
    img = Image.open(SRC / "fig22_asteroids.png").convert("RGBA")
    out = add_panel(
        img,
        "Asteroid resource mining",
        [
            ("Asteroid 6178 1986 DA", "— main metal source"),
            ("Automated mining operations", "and delivery to station"),
        ],
    )
    out.save(DST / "fig22_asteroids.png")


def make_fig23() -> None:
    img = Image.open(SRC / "fig23_quarantine.png").convert("RGBA")
    out = add_panel(
        img,
        "Station quarantine zone",
        [
            ("Isolation", "of new objects and personnel"),
            ("Biological protection", "of station ecosystem"),
        ],
    )
    out.save(DST / "fig23_quarantine.png")


def make_fig24() -> None:
    img = Image.open(SRC / "fig24_panel_choice.png").convert("RGBA")
    out = add_panel(
        img,
        "Radiator panel selection",
        [
            ("Materials", "area and placement on frame"),
            ("Optimization", "of heat rejection and mass"),
        ],
    )
    out.save(DST / "fig24_panel_choice.png")


if __name__ == "__main__":
    make_fig01()
    print("fig01 done")
    make_fig02()
    print("fig02 copied (already English)")
    make_fig03()
    print("fig03 done")
    make_fig04()
    print("fig04 done")
    make_fig05()
    print("fig05 done")
    make_fig06()
    print("fig06 done")
    make_fig07()
    print("fig07 done")
    make_fig08()
    print("fig08 done")
    make_fig09()
    print("fig09 done")
    make_fig10()
    print("fig10 copied (already English)")
    make_fig11()
    print("fig11 done")
    make_fig12()
    print("fig12 done")
    make_fig13()
    print("fig13 done")
    make_fig14()
    print("fig14 done")
    make_fig15()
    print("fig15 done")
    make_fig16()
    print("fig16 done")
    make_fig17()
    print("fig17 copied (already English)")
    make_fig18()
    print("fig18 done")
    make_fig19()
    print("fig19 done")
    make_fig20()
    print("fig20 done")
    make_fig21()
    print("fig21 done")
    make_fig22()
    print("fig22 done")
    make_fig23()
    print("fig23 done")
    make_fig24()
    print("fig24 done")
