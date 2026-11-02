#!/usr/bin/env python3
"""Наложение английских подписей на чистые версии картинок галереи.

Сохраняет графику неизменной, добавляя английскую текстовую панель справа.
Картинки, где английский текст уже присутствует (fig02, fig10, fig17),
копируются как есть.
"""

from __future__ import annotations

import shutil
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

SRC = Path("site/assets/fig")
DST = Path("site/assets/fig_en")
DST.mkdir(exist_ok=True)

try:
    FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    FONT_REG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    FONT_WARN = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except Exception:
    FONT_TITLE = ImageFont.load_default()
    FONT_REG = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()
    FONT_WARN = ImageFont.load_default()


PANEL_W = 700  # достаточно широкая панель, чтобы текст не обрезался


def add_panel(img: Image.Image, title: str, lines: list[tuple[str, str | None]],
              warn_lines: list[str] | None = None) -> Image.Image:
    """Добавляет текстовую панель шириной PANEL_W справа."""
    w, h = img.size
    canvas = Image.new("RGBA", (w + PANEL_W, h), (255, 255, 255, 255))
    canvas.paste(img, (0, 0))
    draw = ImageDraw.Draw(canvas)

    x = w + 30
    y = 30

    # Заголовок
    draw.text((x, y), title, font=FONT_TITLE, fill=(20, 20, 20, 255))
    y += 55

    for label, value in lines:
        if label is None and value is None:
            y += 12
            continue
        draw.text((x, y), label, font=FONT_REG, fill=(50, 50, 50, 255))
        if value:
            draw.text((x + 340, y), value, font=FONT_REG, fill=(80, 80, 80, 255))
        y += 40

    if warn_lines:
        y += 20
        for wl in warn_lines:
            draw.text((x, y), wl, font=FONT_WARN, fill=(180, 40, 40, 255))
            y += 36

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


if __name__ == "__main__":
    # fig02_section уже на английском — копируем как есть
    shutil.copy2(SRC / "fig02_section.png", DST / "fig02_section.png")
    print("fig02 copied (already English)")

    # fig10_energy и fig17_food уже содержат английский текст — копируем как есть
    shutil.copy2(SRC / "fig10_energy.png", DST / "fig10_energy.png")
    print("fig10 copied (already English)")
    shutil.copy2(SRC / "fig17_food.png", DST / "fig17_food.png")
    print("fig17 copied (already English)")

    make_fig01()
    print("fig01 done")
    make_fig04()
    print("fig04 done")
    make_fig15()
    print("fig15 done")
    make_fig16()
    print("fig16 done")
    make_fig18()
    print("fig18 done")
