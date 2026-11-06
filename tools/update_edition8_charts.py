#!/usr/bin/env python3
"""Regenerate selected Edition 8 gallery charts from the combined bilingual DOCX files.

The generator updates figures 03–04, 06–13 and 16 from numerical tables, and
figures 17–24 from tables, documented numeric text, equations, and diagrams.
Figures 01–02, 05 and 14–15 remain unchanged as schematics or model plots
outside the selected scope. Figure 03 derives the radial gravity/speed profile
from the 5 km, 0.423 rpm MMOSO'N row in Table 25.1. Numeric data are extracted
independently from both localized documents and must agree before images are
written.

Default mode writes review PNGs under build/edition8-chart-preview/ and does
not change the website or documents. Use --apply to replace the selected PNGs
in site/assets/fig_ru and fig_en and rebuild the self-contained site pages. Add
--sync-docx to also replace the matching embedded images in both combined DOCX
files, keeping their existing picture relationships and layout dimensions.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = {
    "ru": ROOT / "sections" / "MMOSON_combined_document_ru.docx",
    "en": ROOT / "sections" / "MMOSON_combined_document_en.docx",
}
ASSET_DIRS = {
    "ru": ROOT / "site" / "assets" / "fig_ru",
    "en": ROOT / "site" / "assets" / "fig_en",
}
PREVIEW_DIR = ROOT / "build" / "edition8-chart-preview"

# These are the only assets this tool is allowed to redraw.
FIGURES = (
    "fig03_gravity",
    "fig04_climate",
    "fig06_steel",
    "fig07_load",
    "fig08_mass",
    "fig09_thermal",
    "fig10_energy",
    "fig11_docking",
    "fig12_coriolis",
    "fig13_climb",
    "fig16_resources",
    "fig17_food",
    "fig18_land",
    "fig19_epidemic",
    "fig20_acoustics",
    "fig21_volatiles",
    "fig22_asteroids",
    "fig23_quarantine",
    "fig24_panel_choice",
)
FIGURE_TITLE_KEYS = {
    "fig03_gravity": "gravity",
    "fig04_climate": "climate",
    "fig06_steel": "steel",
    "fig07_load": "load",
    "fig08_mass": "mass",
    "fig09_thermal": "thermal",
    "fig10_energy": "energy",
    "fig11_docking": "docking",
    "fig12_coriolis": "coriolis",
    "fig13_climb": "climb",
    "fig16_resources": "resources",
    "fig17_food": "food",
    "fig18_land": "land",
    "fig19_epidemic": "epidemic",
    "fig20_acoustics": "acoustics",
    "fig21_volatiles": "volatiles",
    "fig22_asteroids": "asteroids",
    "fig23_quarantine": "quarantine",
    "fig24_panel_choice": "panel_choice",
}

COLORS = {
    "navy": (47, 83, 117),
    "blue": (73, 119, 162),
    "sky": (104, 158, 185),
    "teal": (35, 150, 119),
    "green": (72, 135, 92),
    "gold": (199, 151, 47),
    "red": (184, 76, 57),
    "gray": (112, 119, 128),
    "light": (232, 235, 239),
    "dark": (37, 44, 52),
    "muted": (103, 108, 116),
    "white": (255, 255, 255),
}
ZONE_COLORS = (
    (39, 148, 98),
    (136, 181, 74),
    (202, 162, 57),
    (107, 165, 194),
)

LANG_TEXT = {
    "ru": {
        "gravity": "Гравитация и окружная скорость · таблица 25.1",
        "gravity_radius": "Расстояние от оси, км",
        "gravity_g": "Местная тяжесть, g",
        "gravity_speed": "Окружная скорость, м/с",
        "climate": "Климатические зоны цилиндра · таблица 2.1",
        "steel": "Применимость марок стали · таблица 4.1",
        "load": "Расчётная нагрузка и напряжение · редакция 8",
        "mass": "Массовый баланс станции · редакция 8",
        "thermal": "Площадь радиатора при разной температуре · редакция 8",
        "energy": "Энергетический баланс станции · таблицы 4.15 и световых зон",
        "docking": "Скорость и ускорение по радиусу · таблица 4.8",
        "coriolis": "Ускорение Кориолиса при переходе «ось — обод» · таблица 4.10",
        "climb": "Работа подъёма по участкам · таблица 4.9",
        "resources": "Потребность в материалах · таблица 4.14",
        "food": "Продовольственный баланс и вклад культур · таблицы 5.2 и 5.4",
        "land": "Баланс землепользования · таблица 5.5",
        "epidemic": "Эпидемия и коллективный иммунитет · модель SIR",
        "acoustics": "Собственные частоты станции и слышимый диапазон",
        "volatiles": "Сырьё для воды и атмосферных газов",
        "asteroids": "Ресурсные тела: орбитальные диапазоны",
        "quarantine": "Карантинный контур: четыре потока, три ступени",
        "panel_choice": "Выбор размера панели: швы и масса отливки",
        "food_calories": "Энергия, трлн ккал/год",
        "food_protein": "Белок, тыс. т/год",
        "food_need": "Потребность",
        "food_reserve": "С резервом",
        "food_output": "Продукция (нетто)",
        "crop_total": "Вклад культур, млрд ккал (итого 2 216)",
        "land_area": "Площадь, км²",
        "epidemic_attack": "Переболеют без мер, %",
        "epidemic_threshold": "Порог коллективного иммунитета, %",
        "epidemic_r0": "Базовое репродуктивное число R₀",
        "frequency": "Частота, Гц (логарифмическая шкала)",
        "sound_band": "Полоса слышимого звука: 20 Гц — 20 кГц",
        "mode_long": "Продольная мода объёма",
        "mode_trans": "Поперечная мода объёма",
        "mode_shell": "Кольцевая мода стальной оболочки",
        "raw_materials": "Потребное сырьё, млрд т",
        "oxygen_option": "O₂ из силикатного реголита",
        "water_option": "Вода из CI-хондритов (20%)",
        "nitrogen_rock_option": "N₂ из углистых хондритов (0,15%)",
        "nitrogen_comet_option": "N₂ из кометных льдов (1%)",
        "station_mass": "Масса станции 46,70 млрд т",
        "alternative_atmosphere": "70 кПа · 30% O₂: атмосфера 5,26 млрд т; N₂ 3,53 млрд т",
        "orbit_distance": "Расстояние от Солнца, а.е.",
        "quarantine_stage_1": "I · Проверка",
        "quarantine_stage_2": "II · Изоляция / обработка",
        "quarantine_stage_3": "III · Допуск по результатам",
        "flow_people": "Люди",
        "flow_living": "Живое: семена, биота, насекомые",
        "flow_cargo": "Грузы и оборудование",
        "flow_air_water": "Воздух и вода шлюза",
        "quarantine_channel": "Один общий осевой канал Ø8 м",
        "quarantine_capacity": "потока 100 000 человек/год · 40 суток · 10 951 место единовременно",
        "panel_width": "Ширина панели, м",
        "panel_seams": "Длина швов, тыс. км",
        "panel_mass": "Масса панели, тыс. т",
        "panel_accepted": "Принято 50 × 100 м",
        "panel_note": "Кривизна 62 мм · заливка 17 мин · 251 327 панелей/цилиндр",
        "distance": "Расстояние от торца цилиндра, км",
        "temperature": "Температура, °C",
        "steel_strength": "Предел прочности, МПа",
        "steel_allowable": "Допускаемое напряжение, МПа",
        "load_components": "Компоненты нагрузки, кПа",
        "stress_limits": "Кольцевое напряжение и пределы стали, МПа",
        "mass_components": "Масса, млрд т",
        "radiator_area": "Потребная площадь, км²",
        "radiator_temp": "Температура радиатора, °C",
        "power_consumers": "Потребители электрической мощности, ГВт",
        "zone_power": "Мощность светового потока по зонам, ГВт",
        "radius": "Расстояние от оси, км",
        "linear_speed": "Линейная скорость, м/с",
        "acceleration": "Местная тяжесть, g",
        "coriolis_g": "Ускорение Кориолиса, g",
        "work": "Работа, Дж/кг",
        "share": "Доля работы, %",
        "material_need": "Потребность, млрд т",
        "table_source": "Источник данных: объединённая документация редакции 8.",
        "total": "ИТОГО",
        "calorie": "Потребность / запас / продукция, трлн ккал/год",
        "protein": "Потребность / запас / продукция, тыс. т/год",
        "crops": "Калорийный выход культур, млрд ккал/год",
        "zone": "Зона",
        "share_in_label": "доля",
        "yield": "Продукция",
    },
    "en": {
        "gravity": "Gravity and rim speed · Table 25.1",
        "gravity_radius": "Distance from axis, km",
        "gravity_g": "Local gravity, g",
        "gravity_speed": "Tangential speed, m/s",
        "climate": "Cylinder climate zones · Table 2.1",
        "steel": "Applicability of steel grades · Table 4.1",
        "load": "Design load and stress · Edition 8",
        "mass": "Station mass balance · Edition 8",
        "thermal": "Radiator area by temperature · Edition 8",
        "energy": "Station energy balance · Table 4.15 and lighting zones",
        "docking": "Velocity and acceleration by radius · Table 4.8",
        "coriolis": "Coriolis acceleration during axis-to-rim transit · Table 4.10",
        "climb": "Lifting work by route segment · Table 4.9",
        "resources": "Material requirements · Table 4.14",
        "food": "Food balance and crop contributions · Tables 5.2 and 5.4",
        "land": "Land-use balance · Table 5.5",
        "epidemic": "Epidemic spread and herd immunity · SIR model",
        "acoustics": "Station natural frequencies and audible range",
        "volatiles": "Feedstock for water and atmospheric gases",
        "asteroids": "Resource bodies: orbital distance ranges",
        "quarantine": "Quarantine circuit: four streams, three stages",
        "panel_choice": "Panel-size selection: weld length and casting mass",
        "food_calories": "Energy, trillion kcal/year",
        "food_protein": "Protein, thousand tons/year",
        "food_need": "Need",
        "food_reserve": "With reserve",
        "food_output": "Net products",
        "crop_total": "Crop energy contribution, billion kcal (total 2,216)",
        "land_area": "Area, km²",
        "epidemic_attack": "Infected without intervention, %",
        "epidemic_threshold": "Herd-immunity threshold, %",
        "epidemic_r0": "Basic reproduction number R₀",
        "frequency": "Frequency, Hz (log scale)",
        "sound_band": "Audible range: 20 Hz — 20 kHz",
        "mode_long": "Longitudinal air-volume mode",
        "mode_trans": "Transverse air-volume mode",
        "mode_shell": "Steel-shell ring mode",
        "raw_materials": "Required raw material, billion tons",
        "oxygen_option": "O₂ from silicate regolith",
        "water_option": "Water from CI chondrites (20%)",
        "nitrogen_rock_option": "N₂ from carbonaceous chondrites (0.15%)",
        "nitrogen_comet_option": "N₂ from cometary ice (1%)",
        "station_mass": "Station mass: 46.70 billion tons",
        "alternative_atmosphere": "70 kPa · 30% O₂: atmosphere 5.26 billion tons; N₂ 3.53 billion tons",
        "orbit_distance": "Heliocentric distance, AU",
        "quarantine_stage_1": "I · Screening",
        "quarantine_stage_2": "II · Isolation / processing",
        "quarantine_stage_3": "III · Release after tests",
        "flow_people": "People",
        "flow_living": "Living organisms: seeds, biota, insects",
        "flow_cargo": "Cargo and equipment",
        "flow_air_water": "Air and airlock water",
        "quarantine_channel": "One shared axial channel Ø8 m",
        "quarantine_capacity": "Flow of 100,000 people/year · 40 days · 10,951 concurrent places",
        "panel_width": "Panel width, m",
        "panel_seams": "Weld length, thousand km",
        "panel_mass": "Panel mass, thousand tons",
        "panel_accepted": "Selected: 50 × 100 m",
        "panel_note": "62 mm camber · 17 min pour · 251,327 panels/cylinder",
        "distance": "Distance from cylinder end, km",
        "temperature": "Temperature, °C",
        "steel_strength": "Tensile strength, MPa",
        "steel_allowable": "Allowable stress, MPa",
        "load_components": "Load components, kPa",
        "stress_limits": "Hoop stress and steel limits, MPa",
        "mass_components": "Mass, billion tons",
        "radiator_area": "Required area, km²",
        "radiator_temp": "Radiator temperature, °C",
        "power_consumers": "Electricity consumers, GW",
        "zone_power": "Lighting power by climate zone, GW",
        "radius": "Distance from axis, km",
        "linear_speed": "Linear speed, m/s",
        "acceleration": "Local gravity, g",
        "coriolis_g": "Coriolis acceleration, g",
        "work": "Work, J/kg",
        "share": "Share of work, %",
        "material_need": "Demand, billion tons",
        "table_source": "Data source: combined Edition 8 documentation.",
        "total": "TOTAL",
        "calorie": "Need / reserve / output, trillion kcal/year",
        "protein": "Need / reserve / output, thousand tons/year",
        "crops": "Crop energy output, billion kcal/year",
        "zone": "Zone",
        "share_in_label": "share",
        "yield": "Output",
    },
}


@dataclass(frozen=True)
class TableRecord:
    index: int
    caption: str
    rows: tuple[tuple[str, ...], ...]

    @property
    def header(self) -> tuple[str, ...]:
        return self.rows[0] if self.rows else ()


class TableCatalog:
    """Index top-level Word tables together with their immediately preceding captions."""

    def __init__(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError(f"missing Edition 8 document: {path.relative_to(ROOT)}")
        self.path = path
        self.document = Document(path)
        self.paragraphs = [
            " ".join(Paragraph(element, self.document).text.split())
            for element in self.document.element.body.iter(qn("w:p"))
            if Paragraph(element, self.document).text.strip()
        ]
        self.records: list[TableRecord] = []
        pending_caption = ""
        table_number = 0
        for block in self.document.element.body.iterchildren():
            if block.tag == qn("w:p"):
                text = " ".join(Paragraph(block, self.document).text.split())
                folded = text.casefold()
                if folded.startswith(("таблица ", "table ")):
                    pending_caption = text
                elif folded.startswith(("рисунок ", "figure ")):
                    pending_caption = ""
            elif block.tag == qn("w:tbl"):
                table_number += 1
                table = Table(block, self.document)
                rows = tuple(
                    tuple(" ".join(cell.text.split()) for cell in row.cells)
                    for row in table.rows
                )
                self.records.append(TableRecord(table_number, pending_caption, rows))
                pending_caption = ""

    def by_caption(self, number: str) -> TableRecord:
        pattern = re.compile(
            rf"^(?:таблица|table)\s+{re.escape(number)}\b",
            re.IGNORECASE,
        )
        matches = [record for record in self.records if pattern.search(record.caption)]
        return self._one(matches, f"caption {number}")

    def by_headers(self, *header_groups: tuple[str, ...]) -> TableRecord:
        matches = []
        for record in self.records:
            header_text = tuple(_norm(cell) for cell in record.header)
            if not header_text:
                continue
            if all(
                any(_norm(alias) in cell for alias in group for cell in header_text)
                for group in header_groups
            ):
                matches.append(record)
        return self._one(matches, "headers " + "; ".join("/".join(g) for g in header_groups))

    @staticmethod
    def _one(matches: list[TableRecord], description: str) -> TableRecord:
        if len(matches) != 1:
            details = ", ".join(f"table {m.index}: {m.caption or '<uncaptioned>'}" for m in matches)
            raise ValueError(
                f"expected exactly one Edition 8 table for {description}; found {len(matches)}"
                + (f" ({details})" if details else "")
            )
        return matches[0]


def _norm(text: str) -> str:
    return " ".join(text.casefold().replace("ё", "е").split())


def _column(table: TableRecord, *aliases: str) -> int:
    for index, header in enumerate(table.header):
        folded = _norm(header)
        if any(_norm(alias) in folded for alias in aliases):
            return index
    raise ValueError(
        f"table {table.index} ({table.caption or 'uncaptioned'}) has no column matching {aliases!r}; "
        f"headers={table.header!r}"
    )


def _cell(row: tuple[str, ...], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


_NUMBER_RE = re.compile(r"[-+−]?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?")


def _parse_token(token: str, comma_mode: str = "decimal") -> float:
    token = token.strip().replace("\u00a0", " ").replace("\u202f", " ")
    token = token.replace("−", "-").replace(" ", "")
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(",", "" if comma_mode == "group" else ".")
    try:
        return float(token)
    except ValueError as exc:
        raise ValueError(f"cannot parse number {token!r}") from exc


def _first_number(text: str, comma_mode: str = "decimal") -> float:
    match = _NUMBER_RE.search(text.replace("−", "-"))
    if not match:
        raise ValueError(f"no number in cell {text!r}")
    return _parse_token(match.group(0), comma_mode)


def _unsigned_numbers(text: str) -> list[float]:
    tokens = re.findall(r"\d+(?:[.,]\d+)?", text)
    return [_parse_token(token, "decimal") for token in tokens]


def _signed_numbers(text: str) -> list[float]:
    normalized = text.replace("−", "-").replace("–", "-")
    tokens = re.findall(r"[-+]?\d+(?:[.,]\d+)?", normalized)
    return [_parse_token(token, "decimal") for token in tokens]


def _range(text: str, signed: bool = False) -> tuple[float, float]:
    values = _signed_numbers(text) if signed else _unsigned_numbers(text)
    if not values:
        raise ValueError(f"expected a numeric value or range in {text!r}")
    if len(values) == 1:
        return values[0], values[0]
    return min(values[0], values[1]), max(values[0], values[1])


_TEXT_NUMBER_RE = re.compile(r"(?<![\w])[-+−]?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?")


def _text_numbers(text: str) -> list[float]:
    values = []
    for match in _TEXT_NUMBER_RE.findall(text.replace("−", "-")):
        compact = match.replace("\u00a0", " ").replace("\u202f", " ").replace(" ", "")
        comma_mode = "group" if re.fullmatch(r"[-+]?\d{1,3}(?:,\d{3})+", compact) else "decimal"
        values.append(_parse_token(match, comma_mode=comma_mode))
    return values


def _find_paragraph(catalog: TableCatalog, *phrases: str) -> str:
    needles = tuple(_norm(phrase) for phrase in phrases)
    for paragraph in catalog.paragraphs:
        folded = _norm(paragraph)
        if all(needle in folded for needle in needles):
            return paragraph
    raise ValueError(
        f"{catalog.path.name}: could not find narrative paragraph containing {phrases!r}"
    )


def _paragraph_number(text: str, pattern: str, description: str, comma_mode: str = "auto") -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"could not extract {description} from paragraph: {text[:180]!r}")
    token = match.group(1)
    if comma_mode == "auto":
        compact = token.replace(" ", "")
        comma_mode = "group" if re.fullmatch(r"\d{1,3}(?:,\d{3})+", compact) else "decimal"
    return _parse_token(token, comma_mode=comma_mode)


def _is_total(label: str) -> bool:
    folded = _norm(label)
    return (
        folded.startswith(("итого", "всего", "total", "sum"))
        or "qtotal" in folded
        or "qext" in folded
    )


def extract_edition_data(language: str, catalog: TableCatalog) -> dict[str, Any]:
    """Read and normalize the table-backed datasets used by figures 04, 06–13 and 16."""
    data: dict[str, Any] = {}

    # Figure 03 — derive the radial profile from the MMOSO'N design row in Table 25.1.
    gravity_table = catalog.by_caption("25.1")
    c_design_radius = _column(gravity_table, "R, м", "R, m")
    c_rpm = _column(gravity_table, "об/мин", "rpm")
    design_radius = None
    design_rpm = None
    for row in gravity_table.rows[1:]:
        radius_text = _cell(row, c_design_radius)
        radius = _first_number(radius_text, comma_mode="group") if radius_text else None
        if radius is not None and math.isclose(radius, 5000.0, abs_tol=1e-6):
            design_radius = radius
            design_rpm = _first_number(_cell(row, c_rpm), comma_mode="decimal")
            break
    if design_radius is None or design_rpm is None:
        raise ValueError("Table 25.1 is missing the 5,000 m MMOSO'N design row")
    omega = 2.0 * math.pi * design_rpm / 60.0
    gravity_points = []
    for radius_m in (0.0, 100.0, 1000.0, 2500.0, design_radius):
        gravity_points.append(
            {
                "label": f"{_number_label(radius_m, language, 0)} m",
                "radius_km": radius_m / 1000.0,
                "gravity": omega * omega * radius_m / 9.80665,
                "speed": omega * radius_m,
            }
        )
    data["fig03_gravity"] = {
        "source_radius_m": design_radius,
        "rpm": design_rpm,
        "points": gravity_points,
    }

    # Figure 04 — climatic bands versus axial distance.
    climate = catalog.by_caption("2.1")
    c_zone = _column(climate, "Зона", "Zone")
    c_distance = _column(climate, "Расстояние", "Distance")
    c_temp = _column(climate, "Температура", "Temperature")
    data["fig04_climate"] = []
    for row in climate.rows[1:]:
        zone = _cell(row, c_zone)
        if not zone:
            continue
        start, end = _range(_cell(row, c_distance))
        temp_min, temp_max = _range(_cell(row, c_temp), signed=True)
        data["fig04_climate"].append(
            {"label": zone, "start": start, "end": end, "temp_min": temp_min, "temp_max": temp_max}
        )

    # Figure 06 — ultimate and allowable stress by steel grade.
    steel = catalog.by_caption("4.1")
    c_grade = _column(steel, "Марка стали", "Steel grade")
    c_strength = _column(steel, "Предел прочности", "Tensile strength")
    c_allowable = _column(steel, "Допускаемое", "Allowable")
    data["fig06_steel"] = []
    for row in steel.rows[1:]:
        grade = _cell(row, c_grade)
        if not grade or _is_total(grade):
            continue
        data["fig06_steel"].append(
            {
                "label": grade,
                "strength": _first_number(_cell(row, c_strength)),
                "allowable": _first_number(_cell(row, c_allowable)),
            }
        )

    # Figure 07 — load component table plus the Edition 8 shell stress table.
    loads = catalog.by_headers(
        ("Компонент нагрузки", "Load component"),
        ("Величина, кПа", "Value, kPa"),
    )
    c_load_name = _column(loads, "Компонент нагрузки", "Load component")
    c_load_value = _column(loads, "Величина, кПа", "Value, kPa")
    load_rows = []
    q_total = None
    for row in loads.rows[1:]:
        label = _cell(row, c_load_name)
        value = _cell(row, c_load_value)
        if not label or not value:
            continue
        if "qtotal" in _norm(label) or "расчетная нагрузка" in _norm(label) or "design load" in _norm(label):
            q_total = _first_number(value)
            continue
        if _is_total(label):
            continue
        load_rows.append({"label": label, "value": _first_number(value)})

    stress = catalog.by_caption("20.2")
    c_position = _column(stress, "Положение", "Position")
    c_stress = _column(stress, "Напряжение", "Stress")
    hoop_stress = None
    for row in stress.rows[1:]:
        label = _norm(_cell(row, c_position))
        if ("середина цилиндрической части" in label) or ("middle of the cylindrical part" in label):
            hoop_stress = _first_number(_cell(row, c_stress))
            break
    if hoop_stress is None:
        raise ValueError("Table 20.2 is missing the cylindrical-part hoop-stress row")

    steel_300 = next(
        row for row in data["fig06_steel"]
        if "18ni(300)" in _norm(row["label"])
    )
    if q_total is None:
        raise ValueError("load component table is missing the total design load qtotal")
    data["fig07_load"] = {
        "parts": load_rows,
        "total": q_total,
        "hoop_stress": hoop_stress,
        "allowable": steel_300["allowable"],
        "strength": steel_300["strength"],
    }

    # Figure 08 — uncaptioned mass balance with per-station component masses.
    mass = catalog.by_headers(
        ("Составляющая", "Component"),
        ("Два цилиндра", "Two cylinders"),
    )
    c_mass_name = _column(mass, "Составляющая", "Component")
    c_mass_value = _column(mass, "Два цилиндра", "Two cylinders")
    mass_rows = []
    station_total = None
    for row in mass.rows[1:]:
        label = _cell(row, c_mass_name)
        value = _cell(row, c_mass_value)
        if not label or not value:
            continue
        if _is_total(label):
            if "станц" in _norm(label) or "station" in _norm(label):
                station_total = _first_number(value)
            continue
        mass_rows.append({"label": label, "value": _first_number(value)})
    if station_total is None:
        raise ValueError("mass balance table is missing the total station mass")
    data["fig08_mass"] = {"parts": mass_rows, "total": station_total}

    # Figure 09 — radiator heat rejection area by radiator temperature.
    thermal = catalog.by_headers(
        ("Температура радиатора", "Radiator temperature"),
        ("Площадь для сброса", "Discharge area"),
    )
    c_radiator_temp = _column(thermal, "Температура радиатора", "Radiator temperature")
    c_radiator_area = _column(thermal, "Площадь для сброса", "Discharge area")
    data["fig09_thermal"] = []
    for row in thermal.rows[1:]:
        temp = _cell(row, c_radiator_temp)
        area = _cell(row, c_radiator_area)
        if temp and area:
            data["fig09_thermal"].append(
                {"temperature": _first_number(temp), "area": _first_number(area)}
            )

    # Figure 10 — station electric consumers and zone lighting output.
    power = catalog.by_caption("4.15")
    c_consumer = _column(power, "Потребитель", "Consumer")
    c_power = _column(power, "Мощность", "Power")
    power_rows = []
    power_total = None
    for row in power.rows[1:]:
        label = _cell(row, c_consumer)
        value = _cell(row, c_power)
        if not label or not value:
            continue
        if _is_total(label):
            power_total = _first_number(value)
            continue
        if "тепловая мощность" in _norm(label) or "thermal power" in _norm(label):
            continue
        if "уносится струей" in _norm(label) or "carried away" in _norm(label):
            continue
        power_rows.append({"label": label, "value": _first_number(value)})
    zones = catalog.by_headers(
        ("Зона", "Zone"),
        ("Плотность потока", "Flux density"),
        ("Мощность", "Power"),
    )
    c_zone_name = _column(zones, "Зона", "Zone")
    c_flux = _column(zones, "Плотность потока", "Flux density")
    c_zone_power = _column(zones, "Мощность", "Power")
    zone_rows = []
    for row in zones.rows[1:]:
        label = _cell(row, c_zone_name)
        if not label or _is_total(label):
            continue
        zone_rows.append(
            {
                "label": label,
                "flux": _first_number(_cell(row, c_flux)),
                "value": _first_number(_cell(row, c_zone_power)),
            }
        )
    if power_total is None:
        raise ValueError("Table 4.15 is missing total electric power")
    data["fig10_energy"] = {
        "consumers": power_rows,
        "total": power_total,
        "zones": zone_rows,
    }

    # Figure 11 — tangential speed and local gravity by radius.
    docking = catalog.by_caption("4.8")
    c_radius = _column(docking, "Расстояние от оси", "Distance from axis")
    c_speed = _column(docking, "Линейная скорость", "Linear speed")
    c_accel = _column(docking, "Ускорение", "Acceleration")
    c_status = _column(docking, "Характеристика", "Characteristic")
    docking_rows = []
    for row in docking.rows[1:]:
        radius_text = _cell(row, c_radius)
        speed_text = _cell(row, c_speed)
        if not radius_text or not speed_text or _is_total(radius_text):
            continue
        docking_rows.append(
            {
                "label": radius_text,
                "radius_km": _first_number(radius_text, comma_mode="group") / 1000.0,
                "speed": _first_number(speed_text),
                # In the bilingual tables comma decimals are retained even in EN.
                "gravity": _first_number(_cell(row, c_accel), comma_mode="decimal"),
                "status": _cell(row, c_status),
            }
        )
    data["fig11_docking"] = docking_rows

    # Figure 12 — Coriolis acceleration by means of transition.
    coriolis = catalog.by_caption("4.10")
    c_method = _column(coriolis, "Способ", "Way")
    c_coriolis = _column(coriolis, "Кориолис", "Coriolis")
    coriolis_rows = []
    for row in coriolis.rows[1:]:
        label = _cell(row, c_method)
        value = _cell(row, c_coriolis)
        if not label or not value or value.strip() in {"—", "-"}:
            continue
        bounds = _range(value)
        coriolis_rows.append({"label": label, "min": bounds[0], "max": bounds[1]})
    data["fig12_coriolis"] = coriolis_rows

    # Figure 13 — lift work and its share by radial segment.
    climb = catalog.by_caption("4.9")
    c_segment = _column(climb, "Участок", "Plot")
    c_work = _column(climb, "Работа", "Work")
    c_share = _column(climb, "Доля", "Share")
    climb_rows = []
    for row in climb.rows[1:]:
        label = _cell(row, c_segment)
        value = _cell(row, c_work)
        if not label or not value or _is_total(label):
            continue
        climb_rows.append(
            {
                "label": label,
                "work": _first_number(value, comma_mode="group"),
                "share": _first_number(_cell(row, c_share)),
            }
        )
    data["fig13_climb"] = climb_rows

    # Figure 16 — material demand by resource category.
    resources = catalog.by_caption("4.14")
    c_material = _column(resources, "Материал", "Material")
    c_demand = _column(resources, "Потребность", "Demand")
    resource_rows = []
    for row in resources.rows[1:]:
        label = _cell(row, c_material)
        value = _cell(row, c_demand)
        if not label or not value or _is_total(label):
            continue
        resource_rows.append({"label": label, "value": _first_number(value)})
    data["fig16_resources"] = resource_rows

    # Figure 17 — food balance and crop output from Tables 5.2 and 5.4.
    food_table = catalog.by_caption("5.2")
    c_indicator = _column(food_table, "Показатель", "Indicator")
    c_need = _column(food_table, "Потребность", "Need")
    c_reserve = _column(food_table, "С резервом", "With reserve")
    c_products = _column(food_table, "Продукция", "Products")
    c_stock = _column(food_table, "Запас", "Stock")
    food_balance: dict[str, dict[str, float]] = {}
    for row in food_table.rows[1:]:
        indicator = _norm(_cell(row, c_indicator))
        if not indicator:
            continue
        key = "calories" if ("калор" in indicator or "calor" in indicator) else (
            "protein" if ("белок" in indicator or "protein" in indicator) else None
        )
        if key:
            food_balance[key] = {
                "need": _first_number(_cell(row, c_need)),
                "reserve": _first_number(_cell(row, c_reserve)),
                "output": _first_number(_cell(row, c_products)),
                "stock": _first_number(_cell(row, c_stock)),
            }
    if set(food_balance) != {"calories", "protein"}:
        raise ValueError("Table 5.2 must contain calorie and protein balance rows")

    crop_table = catalog.by_caption("5.4")
    c_crop = _column(crop_table, "Культура", "Culture")
    c_crop_area = _column(crop_table, "Площадь", "Area")
    c_crop_kcal = _column(crop_table, "Ккал", "Kcal")
    crops = []
    crop_total_area = None
    crop_total_kcal = None
    for row in crop_table.rows[1:]:
        label = _cell(row, c_crop)
        if not label:
            continue
        if _is_total(label):
            crop_total_area = _first_number(_cell(row, c_crop_area), comma_mode="group")
            crop_total_kcal = _first_number(_cell(row, c_crop_kcal), comma_mode="group")
            continue
        crops.append(
            {
                "label": label,
                "area": _first_number(_cell(row, c_crop_area), comma_mode="group"),
                "kcal": _first_number(_cell(row, c_crop_kcal), comma_mode="group"),
            }
        )
    if crop_total_area is None or crop_total_kcal is None:
        raise ValueError("Table 5.4 is missing its total row")
    data["fig17_food"] = {
        "balance": food_balance,
        "crops": crops,
        "crop_total_area": crop_total_area,
        "crop_total_kcal": crop_total_kcal,
    }

    # Figure 18 — distinct land-use categories; subtotal/total rows are retained as checks.
    land_table = catalog.by_caption("5.5")
    c_category = _column(land_table, "Категория", "Category")
    c_land_area = _column(land_table, "Площадь", "Area")
    c_land_share = _column(land_table, "Доля", "Share")
    land_parts = []
    agricultural_total = None
    farmland_total = None
    for row in land_table.rows[1:]:
        label = _cell(row, c_category)
        area = _cell(row, c_land_area)
        share = _cell(row, c_land_share)
        if not label or not area:
            continue
        normalized = _norm(label)
        area_value = _first_number(area, comma_mode="group")
        share_value = _first_number(share) if share else None
        if normalized.startswith(("итого сельскохозяйственное", "total agricultural")):
            agricultural_total = area_value
            continue
        if normalized.startswith(("всего сельхозугодий", "total farmland")):
            farmland_total = area_value
            continue
        land_parts.append({"label": label, "area": area_value, "share": share_value})
    if agricultural_total is None or farmland_total is None:
        raise ValueError("Table 5.5 is missing agricultural or total farmland subtotal")
    data["fig18_land"] = {
        "parts": land_parts,
        "agricultural_total": agricultural_total,
        "total": farmland_total,
    }

    data.update(extract_narrative_figure_data(language, catalog, data))
    _validate_language_data(language, data)
    return data


def extract_narrative_figure_data(
    language: str,
    catalog: TableCatalog,
    table_data: dict[str, Any],
) -> dict[str, Any]:
    """Extract figure data documented in prose, or calculate it from stated equations."""
    is_ru = language == "ru"
    result: dict[str, Any] = {}

    # Figure 19 — final epidemic size and herd-immunity threshold (SIR equations).
    sir_text = _find_paragraph(
        catalog,
        "Расчёт по модели SIR" if is_ru else "Calculation using the SIR model",
    )
    r0_tokens = re.findall(r"R[₀0]\s*=\s*(\d+(?:[.,]\d+)?)", sir_text, flags=re.IGNORECASE)
    r0_values = [_parse_token(token, "decimal") for token in r0_tokens]
    if len(r0_values) < 4:
        raise ValueError(f"{catalog.path.name}: SIR paragraph must document four R₀ cases")
    r0_values = r0_values[:4]
    population_text = _find_paragraph(
        catalog,
        "популяция в 500 000 человек" if is_ru else "closed population of 500,000 people",
    )
    population = next((value for value in _text_numbers(population_text) if math.isclose(value, 500000)), None)
    if population is None:
        raise ValueError("SIR population reference of 500,000 people was not found")

    def final_size(r0: float) -> float:
        if r0 <= 1:
            return 0.0
        low, high = 0.0, 1.0
        for _ in range(100):
            mid = (low + high) / 2.0
            residual = 1.0 - math.exp(-r0 * mid) - mid
            if residual > 0:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    section_text = _find_paragraph(
        catalog,
        "при делении на четыре части" if is_ru else "when divided into four parts",
    )
    if ("сорок" not in _norm(section_text) if is_ru else "forty" not in _norm(section_text)):
        raise ValueError("sectioning text is missing the 40-section scenario")
    result["fig19_epidemic"] = {
        "population": population,
        "r0": r0_values,
        "attack": [final_size(value) for value in r0_values],
        "threshold": [1.0 - 1.0 / value for value in r0_values],
        "sections": [4.0, 40.0],
        "section_capacity": [population / 4.0, population / 40.0],
    }

    # Figure 20 — frequencies calculated from the dimensions and constants in Section 7.2.
    dimensions_text = _find_paragraph(
        catalog,
        "оболочка диаметром 10 км" if is_ru else "shell with a diameter of 10 km",
        "длиной 40 км" if is_ru else "40 km long",
    )
    dimension_values = _text_numbers(dimensions_text)
    diameter_km = next((value for value in dimension_values if math.isclose(value, 10.0)), None)
    length_km = next((value for value in dimension_values if math.isclose(value, 40.0)), None)
    if diameter_km is None or length_km is None:
        raise ValueError("acoustic calculation requires the documented 10 km diameter and 40 km length")
    acoustic_text = _find_paragraph(
        catalog,
        "Продольные моды воздушного объёма" if is_ru else "Longitudinal modes of the air volume",
    )
    if ("343 м/с" not in acoustic_text if is_ru else "343 m/s" not in acoustic_text):
        raise ValueError("acoustic source text is missing the documented sound speed of 343 m/s")
    sound_speed = 343.0
    length_m = length_km * 1000.0
    diameter_m = diameter_km * 1000.0
    shell_radius_m = diameter_m / 2.0
    steel_modulus = 2.0e11
    steel_density = 7850.0
    mode_values = [
        {"kind": "long", "order": 1, "frequency": sound_speed / (2.0 * length_m)},
        {"kind": "long", "order": 2, "frequency": 2.0 * sound_speed / (2.0 * length_m)},
        {"kind": "long", "order": 3, "frequency": 3.0 * sound_speed / (2.0 * length_m)},
        {"kind": "transverse", "order": 0, "frequency": sound_speed / (2.0 * diameter_m)},
        {"kind": "shell", "order": 0, "frequency": math.sqrt(steel_modulus / steel_density) / (2.0 * math.pi * shell_radius_m)},
    ]
    result["fig20_acoustics"] = {
        "modes": [
            {**mode, "period": 1.0 / mode["frequency"]}
            for mode in mode_values
        ],
        "audible_low": 20.0,
        "audible_high": 20000.0,
        "infrasound_high": 20.0,
    }

    # Figure 21 — gas demand and raw-material requirements stated in Section 8.
    oxygen_text = _find_paragraph(
        catalog,
        "кислородной квоты" if is_ru else "calculated oxygen quota",
        "силикатного реголита" if is_ru else "silicate regolith",
    )
    water_text = _find_paragraph(
        catalog,
        "для получения 1,17 млрд т воды" if is_ru else "to obtain 1.17 billion tons of water",
    )
    nitrogen_rock_text = _find_paragraph(
        catalog,
        "переработка углистых хондритов" if is_ru else "processing of carbonaceous chondrites",
    )
    nitrogen_comet_text = _find_paragraph(
        catalog,
        "кометные льды содержат азотистые" if is_ru else "comet ices contain nitrogenous compounds",
    )
    atmosphere_text = _find_paragraph(
        catalog,
        "атмосферный баланс станции составляет 7,55 млрд т" if is_ru
        else "atmospheric balance of the station is 7.55 billion tons",
    )
    comet_count_text = _find_paragraph(
        catalog,
        "пятидесяти пяти тел такого класса" if is_ru else "fifty-five bodies of this class",
    )
    alternative_text = _find_paragraph(
        catalog,
        "снижении общего давления до 70 кПа" if is_ru else "total pressure is reduced to 70 kPa",
    )
    oxygen_values = _text_numbers(oxygen_text)
    water_values = _text_numbers(water_text)
    rock_values = _text_numbers(nitrogen_rock_text)
    comet_values = _text_numbers(nitrogen_comet_text)
    atmosphere_values = _text_numbers(atmosphere_text)
    alternative_values = _text_numbers(alternative_text)
    if len(oxygen_values) < 2 or len(water_values) < 5 or len(rock_values) < 3 or len(comet_values) < 3 or len(atmosphere_values) < 2 or len(alternative_values) < 4:
        raise ValueError("one of the volatile-resource paragraphs is missing numerical source values")
    comet_count_confirmed = (
        "пятидесяти пяти" in _norm(comet_count_text)
        if is_ru else "fifty-five bodies" in _norm(comet_count_text)
    )
    comet_bodies = 55.0 if comet_count_confirmed else None
    if comet_bodies is None:
        raise ValueError("the cometary resource paragraph is missing its 55-body estimate")
    result["fig21_volatiles"] = {
        "options": [
            {"kind": "oxygen", "need": oxygen_values[0], "raw": oxygen_values[1]},
            {"kind": "water", "need": water_values[0], "raw": water_values[1],
             "alternative_raw": water_values[3], "alternative_content": water_values[4]},
            {"kind": "nitrogen_rock", "need": rock_values[0], "raw": rock_values[2],
             "content_percent": rock_values[1]},
            {"kind": "nitrogen_comet", "need": comet_values[1], "raw": comet_values[2],
             "content_percent": comet_values[0]},
        ],
        "alternative": {
            "pressure_kpa": alternative_values[0],
            "oxygen_percent": alternative_values[1],
            "atmosphere_mass": alternative_values[2],
            "nitrogen_need": alternative_values[3],
        },
        "atmosphere_total": atmosphere_values[0],
        "water_stock": atmosphere_values[1],
        "comet_bodies": comet_bodies,
        "station_mass": table_data["fig08_mass"]["total"],
    }

    # Figure 22 — perihelion/aphelion ranges derived from textual orbital elements.
    def orbital_value(text: str, patterns: tuple[str, ...], description: str, required: bool = True) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return _parse_token(match.group(1), comma_mode="decimal")
        if required:
            raise ValueError(f"could not find {description} in orbital paragraph: {text[:180]!r}")
        return None

    a_patterns = (
        r"(?:a\s*=\s*|semi-major axis\s+|major (?:axis|axle)\s+|большая полуось\s*)(\d+(?:[.,]\d+)?)",
    )
    e_patterns = (
        r"(?:e\s*=\s*|eccentricity\s*=*\s*|эксцентриситет\s*=*\s*)(\d+(?:[.,]\d+)?)",
    )
    i_patterns = (
        r"(?:i\s*=\s*|inclination\s*=*\s*|наклонение\s*=*\s*)(\d+(?:[.,]\d+)?)",
    )
    period_patterns = (
        r"(?:orbital period|period of revolution|period|период(?: обращения)?)\s*=*\s*(\d+(?:[.,]\d+)?)",
    )
    orbital_sources = (
        ("1986 DA", ("1986 DA", "4,7 года" if is_ru else "4.7 years"), "metal", "1986 DA"),
        ("Ceres", ("Церера", "0,079") if is_ru else ("Ceres", "0.079"), "water", "Церера" if is_ru else "Ceres"),
        ("Themis", ("Themis", "0,117") if is_ru else ("Themis", "0.117"), "water", "Themis"),
        ("Hygiea", ("Hygiea", "0,113") if is_ru else ("Hygiea", "0.113"), "nitrogen", "Hygiea"),
        ("67P", ("67P", "0,641") if is_ru else ("67P", "0.641"), "ice", "67P"),
    )
    orbit_labels = {
        "ru": [
            "(6178) 1986 DA · металл",
            "(1) Церера · вода",
            "(24) Themis · вода и органика",
            "(10) Hygiea · азот и силикаты",
            "67P/Чурюмова—Герасименко · лёд",
        ],
        "en": [
            "(6178) 1986 DA · metal",
            "(1) Ceres · water",
            "(24) Themis · water and organics",
            "(10) Hygiea · nitrogen and silicates",
            "67P/Churyumov–Gerasimenko · ice",
        ],
    }
    bodies = []
    for (body_key, phrases, role, anchor), label in zip(orbital_sources, orbit_labels[language]):
        paragraph = _find_paragraph(catalog, *phrases)
        start = _norm(paragraph).find(_norm(anchor))
        if start < 0:
            raise ValueError(f"could not locate {body_key} within its orbital paragraph")
        paragraph = paragraph[start:]
        a = orbital_value(paragraph, a_patterns, f"{body_key} semi-major axis")
        e = orbital_value(paragraph, e_patterns, f"{body_key} eccentricity")
        inclination = orbital_value(paragraph, i_patterns, f"{body_key} inclination")
        period = orbital_value(paragraph, period_patterns, f"{body_key} orbital period", required=False)
        bodies.append({
            "label": label,
            "role": role,
            "a": a,
            "e": e,
            "inclination": inclination,
            "period": period,
            "perihelion": a * (1.0 - e),
            "aphelion": a * (1.0 + e),
        })
    result["fig22_asteroids"] = bodies

    # Figure 23 — four processing streams, capacity, and the shared axial passage.
    capacity_text = _find_paragraph(
        catalog,
        "потока 100 000 человек в год" if is_ru else "flow of 100,000 people per year",
        "10 951 место" if is_ru else "10,951 places",
    )
    capacity_values = _text_numbers(capacity_text)
    annual_flow = next((value for value in capacity_values if math.isclose(value, 100000)), None)
    hold_days = next((value for value in capacity_values if math.isclose(value, 40)), None)
    isolator_places = next((value for value in capacity_values if math.isclose(value, 10951)), None)
    cycles = next((value for value in capacity_values if math.isclose(value, 9.13, abs_tol=0.01)), None)
    block_text = _find_paragraph(
        catalog,
        "занимает 219 000 м²" if is_ru else "occupies 219,000 m²",
        "5 476 боксов" if is_ru else "5,476 boxes",
    )
    block_area = _paragraph_number(
        block_text, r"(?:занимает|occupies)\s*([\d ,]+)\s*(?:м²|m²)", "quarantine block area"
    )
    block_boxes = _paragraph_number(
        block_text, r"(?:вмещает|accommodate)\s*([\d ,]+)\s*(?:боксов|boxes)", "quarantine box count"
    )
    channel_text = _find_paragraph(
        catalog,
        "общий канал чистым диаметром 8,0 м" if is_ru else "common channel with a clear diameter of 8.0 m",
    )
    channel_diameter = _paragraph_number(
        channel_text,
        r"(?:диаметром|diameter(?:\s+of)?)\s*(\d+(?:[.,]\d+)?)\s*(?:м|m)",
        "shared channel diameter",
    )
    cargo_text = _find_paragraph(
        catalog,
        "гамма-облучение дозой 25 кГр" if is_ru else "gamma irradiation with a dose of 25 kGy",
        "200 °C",
    )
    cargo_values = _text_numbers(cargo_text)
    gamma_dose = next((value for value in cargo_values if math.isclose(value, 25)), None)
    sterilization_temp = next((value for value in cargo_values if math.isclose(value, 200)), None)
    if None in (annual_flow, hold_days, isolator_places, cycles, gamma_dose, sterilization_temp):
        raise ValueError("quarantine text is missing its documented flow, capacity, or cargo treatment values")
    flow_labels = [
        LANG_TEXT[language]["flow_people"],
        LANG_TEXT[language]["flow_living"],
        LANG_TEXT[language]["flow_cargo"],
        LANG_TEXT[language]["flow_air_water"],
    ]
    result["fig23_quarantine"] = {
        "annual_flow": annual_flow,
        "hold_days": hold_days,
        "places": isolator_places,
        "cycles": cycles,
        "channel_diameter": channel_diameter,
        "block_area": block_area,
        "block_boxes": block_boxes,
        "gamma_dose": gamma_dose,
        "sterilization_temp": sterilization_temp,
        "flows": flow_labels,
        "stages": 3,
    }

    # Figure 24 — weld length and casting mass by panel width, from the documented geometry.
    sizing_text = _find_paragraph(
        catalog,
        "расчёт выполнен для панелей" if is_ru else "calculation was performed for panels",
    )
    accepted_text = _find_paragraph(
        catalog,
        "принят размер панели" if is_ru else "accepted panel size",
        "251" if is_ru else "251",
    )
    casting_text = _find_paragraph(
        catalog,
        "при ширине 50 м" if is_ru else "with a width of 50 m",
        "250 мм" if is_ru else "250 mm",
    )
    _find_paragraph(
        catalog,
        "оболочка диаметром 10 км" if is_ru else "shell with a diameter of 10 km",
        "длиной 40 км" if is_ru else "40 km long",
    )
    width_start = _paragraph_number(sizing_text, r"(?:диапазоне(?: ширины)? от|range from)\s*(\d+)", "minimum panel width")
    width_end = _paragraph_number(sizing_text, r"(?:до|to)\s*(\d+)\s*(?:м|m)", "maximum panel width")
    ratio_match = re.search(
        r"(?:отношением сторон|aspect ratio(?:\s+of)?)\s*1\s*[:/]\s*(\d+(?:[.,]\d+)?)",
        sizing_text, flags=re.IGNORECASE,
    )
    if not ratio_match:
        raise ValueError("panel-sizing paragraph is missing the documented 1:2 aspect ratio")
    aspect_ratio = _parse_token(ratio_match.group(1), comma_mode="decimal")
    accepted_match = re.search(r"(\d+)\s*[×x]\s*(\d+)\s*(?:м|m)", accepted_text, flags=re.IGNORECASE)
    if not accepted_match:
        raise ValueError("panel-size paragraph is missing the accepted panel dimensions")
    accepted_width = float(accepted_match.group(1))
    accepted_length = float(accepted_match.group(2))
    panel_mass = _paragraph_number(
        accepted_text,
        r"(?:масс(?:а|е|ой)|mass)\s*(?:панели\s*)?(?:of\s*)?(?:составляет|is)?\s*([\d ,]+)\s*(?:т(?:онн)?\.?|tons)",
        "accepted panel mass",
    )
    panel_count = _paragraph_number(
        accepted_text,
        r"([\d ,]+)\s*(?:панелей|panels)",
        "panels per cylinder",
    )
    seam_total = _paragraph_number(
        accepted_text,
        r"(?:суммарная длина(?: сварных)? швов|total length of welds)\s*(?:составляет|—|is)?\s*([\d.,]+)",
        "accepted seam length",
    )
    camber_50 = _paragraph_number(
        casting_text,
        r"(?:при ширине 50 м|with a width of 50 m)[^.;]*?(\d+)\s*(?:мм|mm)",
        "50 m panel camber",
    )
    camber_100 = _paragraph_number(
        casting_text,
        r"(?:при 100 м|with 100 m)[^.;]*?(\d+)\s*(?:мм|mm)",
        "100 m panel camber",
    )
    # Select the cylinder dimensions explicitly stated in the acoustic description.
    circumference_radius_m = diameter_km * 500.0
    cylinder_length_m = length_km * 1000.0
    result["fig24_panel_choice"] = {
        "width_min": width_start,
        "width_max": width_end,
        "aspect_ratio": aspect_ratio,
        "accepted_width": accepted_width,
        "accepted_length": accepted_length,
        "accepted_mass": panel_mass,
        "panel_count": panel_count,
        "accepted_seams": seam_total,
        "camber_50": camber_50,
        "camber_100": camber_100,
        "cylinder_radius": circumference_radius_m,
        "cylinder_length": cylinder_length_m,
        "fill_time_50": 17.0,
    }
    return result


def _validate_language_data(language: str, data: dict[str, Any]) -> None:
    expected = set(FIGURES)
    if set(data) != expected:
        raise ValueError(f"{language}: extracted figure set mismatch: {sorted(set(data) ^ expected)}")
    checks = {
        "fig03_gravity": 5,
        "fig04_climate": 4,
        "fig06_steel": 6,
        "fig07_load": 7,
        "fig08_mass": 5,
        "fig09_thermal": 4,
        "fig10_energy": 2,
        "fig11_docking": 6,
        "fig12_coriolis": 3,
        "fig13_climb": 5,
        "fig16_resources": 6,
        "fig17_food": 14,
        "fig18_land": 4,
        "fig19_epidemic": 4,
        "fig20_acoustics": 5,
        "fig21_volatiles": 4,
        "fig22_asteroids": 5,
        "fig23_quarantine": 4,
    }
    for figure, count in checks.items():
        obj = data[figure]
        if figure == "fig03_gravity":
            actual = len(obj["points"])
        elif figure == "fig07_load":
            actual = len(obj["parts"])
        elif figure == "fig08_mass":
            actual = len(obj["parts"])
        elif figure == "fig10_energy":
            actual = len(obj["zones"])
        elif figure == "fig17_food":
            actual = len(obj["crops"])
        elif figure == "fig18_land":
            actual = len(obj["parts"])
        elif figure == "fig19_epidemic":
            actual = len(obj["r0"])
        elif figure == "fig20_acoustics":
            actual = len(obj["modes"])
        elif figure == "fig21_volatiles":
            actual = len(obj["options"])
        elif figure == "fig23_quarantine":
            actual = len(obj["flows"])
        elif isinstance(obj, list):
            actual = len(obj)
        else:
            continue
        if actual < count:
            raise ValueError(f"{language}: {figure} has {actual} rows; at least {count} expected")
    if not math.isclose(data["fig07_load"]["total"], 222.4, abs_tol=0.2):
        raise ValueError(f"{language}: design load differs from the Edition 8 reference (222.4 kPa)")
    if not math.isclose(data["fig08_mass"]["total"], 46.70, abs_tol=0.02):
        raise ValueError(f"{language}: station mass differs from the Edition 8 reference (46.70 billion tons)")
    if not math.isclose(data["fig10_energy"]["total"], 721.4, abs_tol=0.2):
        raise ValueError(f"{language}: electric power differs from the Edition 8 reference (721.4 GW)")
    food = data["fig17_food"]
    if not math.isclose(food["crop_total_area"], 807.0, abs_tol=1e-6):
        raise ValueError(f"{language}: Table 5.4 crop area must total 807 km²")
    if not math.isclose(food["crop_total_kcal"], sum(row["kcal"] for row in food["crops"]), abs_tol=1e-6):
        raise ValueError(f"{language}: Table 5.4 crop calories do not sum to its total")
    land = data["fig18_land"]
    if not math.isclose(sum(row["area"] for row in land["parts"]), land["total"], abs_tol=1e-6):
        raise ValueError(f"{language}: distinct land-use areas do not sum to total farmland")
    if not math.isclose(sum(row["share"] for row in land["parts"]), 100.0, abs_tol=1e-6):
        raise ValueError(f"{language}: land-use shares do not sum to 100 percent")
    if not all(value < data["fig20_acoustics"]["audible_low"] for value in
               (mode["frequency"] for mode in data["fig20_acoustics"]["modes"])):
        raise ValueError(f"{language}: documented natural frequencies should remain below 20 Hz")
    orbits = data["fig22_asteroids"]
    expected_orbits = ((2.82, 0.582, 4.3), (2.77, 0.079, 10.6), (3.15, 0.117, 0.7),
                       (3.14, 0.113, 3.8), (3.46, 0.641, 7.0))
    for body, expected in zip(orbits, expected_orbits):
        if not all(math.isclose(body[key], value, abs_tol=1e-6)
                   for key, value in zip(("a", "e", "inclination"), expected)):
            raise ValueError(f"{language}: orbital elements for {body['label']} do not match the Edition 8 narrative")
    volatiles = data["fig21_volatiles"]
    if not math.isclose(volatiles["atmosphere_total"], 7.55, abs_tol=1e-6) or not math.isclose(volatiles["water_stock"], 1.17, abs_tol=1e-6):
        raise ValueError(f"{language}: atmospheric/water reserve differs from the Edition 8 narrative")
    if not math.isclose(volatiles["comet_bodies"], 55.0, abs_tol=1e-6):
        raise ValueError(f"{language}: cometary option should represent about 55 bodies of 67P class")
    quarantine = data["fig23_quarantine"]
    if not math.isclose(quarantine["places"], 10951.0, abs_tol=1e-6):
        raise ValueError(f"{language}: quarantine capacity must be 10,951 places")
    if not math.isclose(quarantine["block_area"], 219000.0, abs_tol=1e-6) or not math.isclose(quarantine["block_boxes"], 5476.0, abs_tol=1e-6):
        raise ValueError(f"{language}: quarantine block dimensions differ from the Edition 8 narrative")
    panel = data["fig24_panel_choice"]
    if not math.isclose(panel["aspect_ratio"], 2.0, abs_tol=1e-6):
        raise ValueError(f"{language}: panel aspect ratio differs from the documented 1:2 design")
    if not math.isclose(panel["accepted_length"] / panel["accepted_width"], panel["aspect_ratio"], abs_tol=1e-6):
        raise ValueError(f"{language}: accepted panel dimensions do not match the documented aspect ratio")
    if not math.isclose(panel["accepted_mass"], 33575.0, abs_tol=1e-6) or not math.isclose(panel["accepted_seams"], 37.7, abs_tol=1e-6):
        raise ValueError(f"{language}: accepted panel data differ from the documented 50 × 100 m design")
    calculated_seams = (
        (1.0 + 1.0 / panel["aspect_ratio"]) * 2.0 * math.pi
        * panel["cylinder_radius"] * panel["cylinder_length"]
        / panel["accepted_width"] / 1_000_000.0
    )
    if not math.isclose(calculated_seams, panel["accepted_seams"], abs_tol=0.1):
        raise ValueError(f"{language}: panel weld-length geometry does not reproduce the documented total")


def _number_label(value: float, language: str, digits: int = 1) -> str:
    if math.isclose(value, round(value), abs_tol=1e-8):
        result = f"{int(round(value)):,}".replace(",", " ")
    else:
        result = f"{value:,.{digits}f}".replace(",", " ")
        if language == "ru":
            result = result.replace(".", ",")
    return result


@lru_cache(maxsize=64)
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if size < 8:
        size = 8
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
            "C:/Windows/Fonts/georgiab.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
            "C:/Windows/Fonts/georgia.ttf",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    try:
        return ImageFont.truetype("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text or " ", font=font)
    return box[2] - box[0], box[3] - box[1]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int, max_lines: int = 3) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and _text_size(draw, last + "…", font)[0] > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    width: int,
    fill: tuple[int, int, int],
    max_lines: int = 3,
    spacing: int = 3,
) -> int:
    lines = _wrap(draw, text, font, width, max_lines=max_lines)
    draw.multiline_text(xy, "\n".join(lines), font=font, fill=fill, spacing=spacing)
    return len(lines) * (_text_size(draw, "Ag", font)[1] + spacing)


def _canvas(language: str, figure: str, size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    image = Image.new("RGB", size, COLORS["white"])
    draw = ImageDraw.Draw(image)
    scale = max(0.7, min(size[0] / 1500.0, size[1] / 700.0))
    title_font = _font(round(31 * scale), bold=True)
    subtitle_font = _font(round(15 * scale))
    title = LANG_TEXT[language][FIGURE_TITLE_KEYS[figure]]
    title_lines = _wrap(draw, title, title_font, size[0] - round(80 * scale), max_lines=2)
    title_y = round(18 * scale)
    title_h = len(title_lines) * round(40 * scale)
    draw.multiline_text((size[0] // 2, title_y), "\n".join(title_lines), font=title_font,
                        fill=COLORS["dark"], anchor="ma", align="center", spacing=3)
    source = LANG_TEXT[language]["table_source"]
    draw.text((size[0] // 2, title_y + title_h), source, font=subtitle_font,
              fill=COLORS["muted"], anchor="ma")
    rule_y = title_y + title_h + round(24 * scale)
    draw.line((round(40 * scale), rule_y, size[0] - round(40 * scale), rule_y),
              fill=COLORS["light"], width=max(1, round(2 * scale)))
    return image, draw, rule_y + round(18 * scale)


def _ticks(maximum: float, count: int = 4) -> list[float]:
    if maximum <= 0:
        return [0.0, 1.0]
    return [maximum * i / count for i in range(count + 1)]


def _draw_hbars(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    rows: list[tuple[str, float, str]],
    language: str,
    unit: str,
    color: tuple[int, int, int] | None = None,
    max_value: float | None = None,
    label_ratio: float = 0.38,
    value_digits: int = 1,
    min_font: int = 13,
    max_label_lines: int = 2,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 900.0, height / 480.0))
    heading_font = _font(round(22 * scale), bold=True)
    label_font = _font(max(min_font, round(16 * scale)))
    value_font = _font(max(min_font, round(15 * scale)), bold=True)
    draw.text((left, top), title, font=heading_font, fill=COLORS["navy"])
    title_h = _text_size(draw, title, heading_font)[1]
    chart_top = top + title_h + round(22 * scale)
    chart_bottom = bottom - round(37 * scale)
    label_width = round(width * label_ratio)
    plot_left = left + label_width
    plot_right = right - round(82 * scale)
    plot_width = max(30, plot_right - plot_left)
    row_height = (chart_bottom - chart_top) / max(1, len(rows))
    peak = max_value if max_value and max_value > 0 else max((value for _, value, _ in rows), default=1.0)
    peak = peak * 1.12 if not max_value else peak
    peak = max(peak, 1e-9)
    for tick in _ticks(peak, count=4):
        x = plot_left + round(plot_width * tick / peak)
        draw.line((x, chart_top, x, chart_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        label = _number_label(tick, language, digits=value_digits)
        draw.text((x, chart_bottom + round(5 * scale)), label, font=label_font,
                  fill=COLORS["muted"], anchor="ma")
    for index, (label, value, note) in enumerate(rows):
        cy = chart_top + row_height * (index + 0.5)
        lines = _wrap(draw, label, label_font, label_width - round(14 * scale), max_lines=max_label_lines)
        draw.multiline_text((left, int(cy)), "\n".join(lines), font=label_font,
                            fill=COLORS["dark"], anchor="lm", spacing=1)
        bar_height = max(6, min(round(25 * scale), int(row_height * 0.55)))
        x_end = plot_left + round(plot_width * max(0.0, value) / peak)
        bar_color = color or (COLORS["navy"], COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["sky"])[index % 5]
        draw.rounded_rectangle((plot_left, int(cy - bar_height / 2), max(plot_left + 1, x_end),
                                int(cy + bar_height / 2)), radius=max(2, round(4 * scale)), fill=bar_color)
        value_text = _number_label(value, language, digits=value_digits)
        if unit:
            value_text += f" {unit}"
        if note:
            value_text += f" · {note}"
        tx = min(x_end + round(8 * scale), right - round(8 * scale))
        draw.text((tx, int(cy)), value_text, font=value_font, fill=COLORS["dark"], anchor="lm")


def _draw_grouped_hbars(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    labels: list[str],
    series: list[tuple[str, list[float], tuple[int, int, int]]],
    language: str,
    unit: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 900.0, height / 480.0))
    heading_font = _font(round(22 * scale), bold=True)
    label_font = _font(max(14, round(16 * scale)))
    legend_font = _font(max(13, round(14 * scale)))
    value_font = _font(max(12, round(13 * scale)), bold=True)
    draw.text((left, top), title, font=heading_font, fill=COLORS["navy"])
    row_top = top + round(62 * scale)
    label_width = round(width * 0.31)
    plot_left = left + label_width
    plot_right = right - round(65 * scale)
    plot_width = max(30, plot_right - plot_left)
    maximum = max((v for _, vals, _ in series for v in vals), default=1.0) * 1.12
    legend_y = top + _text_size(draw, title, heading_font)[1] + round(18 * scale)
    legend_x = plot_left
    for name, _, color in series:
        draw.rectangle((legend_x, legend_y, legend_x + round(14 * scale), legend_y + round(14 * scale)), fill=color)
        draw.text((legend_x + round(20 * scale), legend_y - round(2 * scale)), name, font=legend_font,
                  fill=COLORS["muted"])
        legend_x += round(width * 0.28)
    chart_top = row_top
    chart_bottom = bottom - round(36 * scale)
    row_height = (chart_bottom - chart_top) / max(1, len(labels))
    for tick in _ticks(maximum, count=4):
        x = plot_left + round(plot_width * tick / maximum)
        draw.line((x, chart_top, x, chart_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((x, chart_bottom + round(4 * scale)), _number_label(tick, language, 0),
                  font=legend_font, fill=COLORS["muted"], anchor="ma")
    for i, label in enumerate(labels):
        cy = chart_top + row_height * (i + 0.5)
        lines = _wrap(draw, label, label_font, label_width - round(10 * scale), max_lines=2)
        draw.multiline_text((left, int(cy)), "\n".join(lines), font=label_font,
                            fill=COLORS["dark"], anchor="lm", spacing=1)
        group_h = min(round(31 * scale), int(row_height * 0.72))
        bar_h = max(5, group_h // len(series) - round(2 * scale))
        total_h = len(series) * (bar_h + round(2 * scale))
        y_start = int(cy - total_h / 2)
        for s_index, (series_name, values, color) in enumerate(series):
            value = values[i]
            y1 = y_start + s_index * (bar_h + round(2 * scale))
            x_end = plot_left + round(plot_width * value / maximum)
            draw.rectangle((plot_left, y1, max(plot_left + 1, x_end), y1 + bar_h), fill=color)
            draw.text((min(x_end + round(6 * scale), right - round(4 * scale)), y1 + bar_h // 2),
                      _number_label(value, language, 0), font=value_font, fill=COLORS["dark"], anchor="lm")


def _draw_line_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    xs: list[float],
    ys: list[float],
    language: str,
    x_label: str,
    x_digits: int = 0,
    y_digits: int = 0,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 900.0, height / 480.0))
    heading_font = _font(round(22 * scale), bold=True)
    tick_font = _font(max(13, round(15 * scale)))
    draw.text((left, top), title, font=heading_font, fill=COLORS["navy"])
    plot_left = left + round(85 * scale)
    plot_right = right - round(40 * scale)
    plot_top = top + round(58 * scale)
    plot_bottom = bottom - round(70 * scale)
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(0.0, min(ys)), max(ys)
    if xmax <= xmin:
        xmax = xmin + 1
    if ymax <= ymin:
        ymax = ymin + 1
    margin = (ymax - ymin) * 0.12
    ymin -= margin * 0.1
    ymax += margin
    for tick in _ticks(ymax, 4):
        y = plot_bottom - round((tick - ymin) / (ymax - ymin) * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(10 * scale), y), _number_label(tick, language, y_digits),
                  font=tick_font, fill=COLORS["muted"], anchor="rm")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    points = []
    for x_value, y_value in zip(xs, ys):
        x = plot_left + round((x_value - xmin) / (xmax - xmin) * (plot_right - plot_left))
        y = plot_bottom - round((y_value - ymin) / (ymax - ymin) * (plot_bottom - plot_top))
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=COLORS["blue"], width=max(3, round(4 * scale)), joint="curve")
    point_r = max(4, round(7 * scale))
    for (x, y), x_value, y_value in zip(points, xs, ys):
        draw.ellipse((x - point_r, y - point_r, x + point_r, y + point_r), fill=COLORS["teal"], outline=COLORS["white"], width=2)
        label = _number_label(y_value, language, y_digits)
        draw.text((x, y - point_r - round(4 * scale)), label, font=tick_font,
                  fill=COLORS["dark"], anchor="ms")
        draw.text((x, plot_bottom + round(6 * scale)), _number_label(x_value, language, x_digits),
                  font=tick_font, fill=COLORS["muted"], anchor="ma")
    draw.text(((plot_left + plot_right) // 2, bottom - round(9 * scale)), x_label,
              font=tick_font, fill=COLORS["muted"], anchor="ms")


def _draw_gravity_profile(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    points: list[dict[str, Any]],
    language: str,
) -> None:
    left, top, right, bottom = box
    scale = max(0.65, min((right - left) / 1000.0, (bottom - top) / 550.0))
    tick_font = _font(max(13, round(16 * scale)))
    label_font = _font(max(13, round(16 * scale)), bold=True)
    plot_left = left + round(95 * scale)
    plot_right = right - round(105 * scale)
    plot_top = top + round(48 * scale)
    plot_bottom = bottom - round(78 * scale)
    max_radius = max(point["radius_km"] for point in points)
    max_gravity = max(point["gravity"] for point in points)
    max_speed = max(point["speed"] for point in points)
    # Choose paired axis limits so the two table-derived linear curves coincide.
    speed_limit = max(250.0, math.ceil(max_speed / 50.0) * 50.0)
    gravity_limit = speed_limit / (max_speed / max_gravity)
    for tick_i in range(6):
        radius = max_radius * tick_i / 5.0
        x = plot_left + round((radius / max_radius) * (plot_right - plot_left))
        draw.line((x, plot_top, x, plot_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((x, plot_bottom + round(7 * scale)), _number_label(radius, language, 0),
                  font=tick_font, fill=COLORS["muted"], anchor="ma")
    for tick_i in range(6):
        gravity = max_gravity * tick_i / 5.0
        y = plot_bottom - round((gravity / gravity_limit) * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(12 * scale), y), _number_label(gravity, language, 1),
                  font=tick_font, fill=COLORS["muted"], anchor="rm")
        speed = speed_limit * tick_i / 5.0
        draw.text((plot_right + round(12 * scale), y), _number_label(speed, language, 0),
                  font=tick_font, fill=COLORS["muted"], anchor="lm")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_right, plot_top, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))

    mapped = []
    for point in points:
        x = plot_left + round((point["radius_km"] / max_radius) * (plot_right - plot_left))
        y = plot_bottom - round((point["gravity"] / gravity_limit) * (plot_bottom - plot_top))
        mapped.append((x, y))
    if len(mapped) > 1:
        draw.line(mapped, fill=COLORS["blue"], width=max(3, round(4 * scale)), joint="curve")
    point_radius = max(5, round(7 * scale))
    for i, (point, (x, y)) in enumerate(zip(points, mapped)):
        draw.ellipse((x - point_radius, y - point_radius, x + point_radius, y + point_radius),
                     fill=COLORS["red"], outline=COLORS["white"], width=max(1, round(2 * scale)))
        if point["radius_km"] == 0:
            continue
        label = (
            f"{_number_label(point['gravity'], language, 3)} g · "
            f"{_number_label(point['speed'], language, 1)} "
            f"{'m/s' if language == 'en' else 'м/с'}"
        )
        offsets = ((105, -36), (115, -36), (110, 48), (-135, 48))
        dx, dy = offsets[min(i - 1, len(offsets) - 1)]
        label_font_size = _text_size(draw, label, label_font)
        cx = min(max(x + dx, plot_left + label_font_size[0] // 2), plot_right - label_font_size[0] // 2)
        cy = min(max(y + dy, plot_top + label_font_size[1]), plot_bottom - label_font_size[1])
        text_w, text_h = label_font_size
        pad = round(7 * scale)
        draw.rounded_rectangle(
            (cx - text_w // 2 - pad, cy - text_h // 2 - pad // 2,
             cx + text_w // 2 + pad, cy + text_h // 2 + pad // 2),
            radius=max(3, round(5 * scale)), fill=COLORS["white"], outline=(205, 208, 212), width=1,
        )
        draw.text((cx, cy), label, font=label_font, fill=COLORS["dark"], anchor="mm")

    draw.text((plot_left, plot_top - round(22 * scale)), LANG_TEXT[language]["gravity_g"],
              font=tick_font, fill=COLORS["navy"], anchor="ls")
    draw.text((plot_right, plot_top - round(22 * scale)), LANG_TEXT[language]["gravity_speed"],
              font=tick_font, fill=COLORS["navy"], anchor="rs")
    draw.text(((plot_left + plot_right) // 2, bottom - round(9 * scale)),
              LANG_TEXT[language]["gravity_radius"], font=tick_font,
              fill=COLORS["muted"], anchor="ms")


def _draw_climate(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], zones: list[dict[str, Any]], language: str) -> None:
    left, top, right, bottom = box
    scale = max(0.65, min((right - left) / 1000.0, (bottom - top) / 550.0))
    tick_font = _font(max(14, round(17 * scale)))
    zone_font = _font(max(14, round(19 * scale)), bold=True)
    plot_left = left + round(105 * scale)
    plot_right = right - round(40 * scale)
    plot_top = top + round(40 * scale)
    plot_bottom = bottom - round(80 * scale)
    x_min, x_max = 0.0, max(zone["end"] for zone in zones)
    y_min = min(zone["temp_min"] for zone in zones) - 5
    y_max = max(zone["temp_max"] for zone in zones) + 5
    if y_min >= 0:
        y_min = -5
    if y_max <= 0:
        y_max = 5
    for tick in range(int(math.floor(y_min / 10) * 10), int(math.ceil(y_max / 10) * 10) + 1, 10):
        y = plot_bottom - round((tick - y_min) / (y_max - y_min) * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(12 * scale), y), str(tick), font=tick_font,
                  fill=COLORS["muted"], anchor="rm")
    for tick in range(0, int(x_max) + 1, 10):
        x = plot_left + round((tick - x_min) / (x_max - x_min) * (plot_right - plot_left))
        draw.line((x, plot_top, x, plot_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((x, plot_bottom + round(8 * scale)), str(tick), font=tick_font,
                  fill=COLORS["muted"], anchor="ma")
    for index, zone in enumerate(zones):
        x0 = plot_left + round((zone["start"] - x_min) / (x_max - x_min) * (plot_right - plot_left))
        x1 = plot_left + round((zone["end"] - x_min) / (x_max - x_min) * (plot_right - plot_left))
        y0 = plot_bottom - round((zone["temp_max"] - y_min) / (y_max - y_min) * (plot_bottom - plot_top))
        y1 = plot_bottom - round((zone["temp_min"] - y_min) / (y_max - y_min) * (plot_bottom - plot_top))
        fill = ZONE_COLORS[index % len(ZONE_COLORS)]
        draw.rectangle((x0, y0, x1, y1), fill=fill, outline=COLORS["white"], width=max(2, round(2 * scale)))
        label = f"{zone['label']}\n{_number_label(zone['temp_min'], language, 0)}…{_number_label(zone['temp_max'], language, 0)} °C"
        draw.multiline_text(((x0 + x1) // 2, (y0 + y1) // 2), label, font=zone_font,
                            fill=COLORS["white"], anchor="mm", align="center", spacing=2)
    draw.text(((plot_left + plot_right) // 2, bottom - round(12 * scale)), LANG_TEXT[language]["distance"],
              font=tick_font, fill=COLORS["muted"], anchor="ms")


def _new_figure(language: str, figure: str, size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    return _canvas(language, figure, size)


def render_figure(figure: str, language: str, data: dict[str, Any], size: tuple[int, int]) -> Image.Image:
    image, draw, content_top = _new_figure(language, figure, size)
    w, h = size
    margin = max(30, round(w * 0.035))
    content_bottom = h - max(35, round(h * 0.04))
    content_left, content_right = margin, w - margin
    gap = max(28, round(w * 0.025))
    lang = LANG_TEXT[language]

    if figure == "fig03_gravity":
        _draw_gravity_profile(draw, (content_left, content_top, content_right, content_bottom),
                              data[figure]["points"], language)
    elif figure == "fig04_climate":
        _draw_climate(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig06_steel":
        rows = data[figure]
        _draw_grouped_hbars(
            draw,
            (content_left, content_top, content_right, content_bottom),
            f"{lang['steel_strength']} / {lang['steel_allowable']}",
            [row["label"] for row in rows],
            [
                (lang["steel_strength"], [row["strength"] for row in rows], COLORS["blue"]),
                (lang["steel_allowable"], [row["allowable"] for row in rows], COLORS["gold"]),
            ],
            language,
            "MPa",
        )
    elif figure == "fig07_load":
        info = data[figure]
        split = content_left + (content_right - content_left) * 0.60
        _draw_hbars(
            draw,
            (content_left, content_top, split - gap // 2, content_bottom),
            f"{lang['load_components']} · qtotal = {_number_label(info['total'], language, 1)} "
            + ("kPa" if language == "en" else "кПа"),
            [(row["label"], row["value"], "") for row in info["parts"]],
            language,
            "kPa",
            max_value=info["total"],
            label_ratio=0.48,
            value_digits=1,
            min_font=12,
        )
        stress_rows = [
            ("Расчётное кольцевое напряжение" if language == "ru" else "Calculated hoop stress", info["hoop_stress"], ""),
            ("Допускаемое напряжение" if language == "ru" else "Allowable stress", info["allowable"], ""),
            ("Предел прочности" if language == "ru" else "Tensile strength", info["strength"], ""),
        ]
        _draw_hbars(
            draw,
            (split + gap // 2, content_top, content_right, content_bottom),
            lang["stress_limits"],
            stress_rows,
            language,
            "MPa",
            max_value=info["strength"],
            label_ratio=0.53,
            value_digits=0,
            min_font=12,
        )
    elif figure == "fig08_mass":
        info = data[figure]
        _draw_hbars(
            draw,
            (content_left, content_top, content_right, content_bottom),
            lang["mass_components"],
            [(row["label"], row["value"], "") for row in info["parts"]],
            language,
            "billion tons" if language == "en" else "млрд т",
            max_value=info["total"],
            label_ratio=0.48,
            value_digits=2,
            max_label_lines=3,
        )
        total_text = f"{lang['total']} — {_number_label(info['total'], language, 2)} " + ("billion tons" if language == "en" else "млрд т")
        draw.text((content_right, content_top + 1), total_text, font=_font(18, bold=True),
                  fill=COLORS["navy"], anchor="rt")
    elif figure == "fig09_thermal":
        points = sorted(data[figure], key=lambda row: row["temperature"])
        _draw_line_chart(
            draw,
            (content_left, content_top, content_right, content_bottom),
            lang["radiator_area"],
            [row["temperature"] for row in points],
            [row["area"] for row in points],
            language,
            lang["radiator_temp"],
            x_digits=0,
            y_digits=0,
        )
    elif figure == "fig10_energy":
        info = data[figure]
        middle = content_top + (content_bottom - content_top) * 0.52
        _draw_hbars(
            draw,
            (content_left, content_top, content_right, middle - gap // 2),
            lang["power_consumers"],
            [(row["label"], row["value"], "") for row in info["consumers"]],
            language,
            "GW",
            max_value=info["total"],
            label_ratio=0.50,
            value_digits=1,
            min_font=12,
        )
        zone_rows = [
            (f"{row['label']} · { _number_label(row['flux'], language, 0)} W/m²", row["value"], "")
            for row in info["zones"]
        ]
        _draw_hbars(
            draw,
            (content_left, middle + gap // 2, content_right, content_bottom),
            lang["zone_power"],
            zone_rows,
            language,
            "GW",
            color=COLORS["teal"],
            max_value=max((row["value"] for row in info["zones"]), default=1) * 1.15,
            label_ratio=0.50,
            value_digits=1,
            min_font=12,
        )
    elif figure == "fig11_docking":
        rows = sorted(data[figure], key=lambda row: row["radius_km"])
        midpoint = content_top + (content_bottom - content_top) * 0.52
        _draw_hbars(
            draw,
            (content_left, content_top, content_right, midpoint - gap // 2),
            lang["linear_speed"],
            [
                (row["label"], row["speed"], "")
                for row in rows
            ],
            language,
            "m/s",
            color=COLORS["blue"],
            label_ratio=0.46,
            value_digits=1,
            min_font=12,
        )
        _draw_hbars(
            draw,
            (content_left, midpoint + gap // 2, content_right, content_bottom),
            lang["acceleration"],
            [(row["label"], row["gravity"], "") for row in rows],
            language,
            "g",
            color=COLORS["gold"],
            max_value=1.0,
            label_ratio=0.46,
            value_digits=3,
            min_font=12,
        )
    elif figure == "fig12_coriolis":
        rows = data[figure]
        _draw_range_bars(
            draw,
            (content_left, content_top, content_right, content_bottom),
            lang["coriolis_g"],
            [(row["label"], row["min"], row["max"]) for row in rows],
            language,
        )
    elif figure == "fig13_climb":
        rows = data[figure]
        _draw_hbars(
            draw,
            (content_left, content_top, content_right, content_bottom),
            lang["work"],
            [
                (
                    row["label"],
                    row["work"],
                    f"{_number_label(row['share'], language, 1)} %",
                )
                for row in rows
            ],
            language,
            "J/kg",
            label_ratio=0.50,
            value_digits=0,
        )
    elif figure == "fig16_resources":
        _draw_hbars(
            draw,
            (content_left, content_top, content_right, content_bottom),
            lang["material_need"],
            [(row["label"], row["value"], "") for row in data[figure]],
            language,
            "billion tons" if language == "en" else "млрд т",
            color=COLORS["green"],
            label_ratio=0.53,
            value_digits=2,
        )
    elif figure == "fig17_food":
        _draw_food_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig18_land":
        _draw_land_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig19_epidemic":
        _draw_epidemic_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig20_acoustics":
        _draw_acoustics_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig21_volatiles":
        _draw_volatiles_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig22_asteroids":
        _draw_orbit_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig23_quarantine":
        _draw_quarantine_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    elif figure == "fig24_panel_choice":
        _draw_panel_choice_figure(draw, (content_left, content_top, content_right, content_bottom), data[figure], language)
    else:
        raise ValueError(f"unsupported figure renderer: {figure}")

    return image


def _draw_range_bars(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    rows: list[tuple[str, float, float]],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1000.0, height / 550.0))
    heading_font = _font(round(22 * scale), bold=True)
    label_font = _font(max(13, round(17 * scale)))
    value_font = _font(max(12, round(14 * scale)))
    draw.text((left, top), title, font=heading_font, fill=COLORS["navy"])
    chart_top = top + round(58 * scale)
    chart_bottom = bottom - round(38 * scale)
    label_width = round(width * 0.40)
    plot_left = left + label_width
    plot_right = right - round(90 * scale)
    plot_width = plot_right - plot_left
    maximum = max((hi for _, _, hi in rows), default=1.0) * 1.2
    row_height = (chart_bottom - chart_top) / max(1, len(rows))
    for tick in _ticks(maximum, 4):
        x = plot_left + round(plot_width * tick / maximum)
        draw.line((x, chart_top, x, chart_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((x, chart_bottom + round(5 * scale)), _number_label(tick, language, 3),
                  font=value_font, fill=COLORS["muted"], anchor="ma")
    for i, (label, low, high) in enumerate(rows):
        cy = chart_top + row_height * (i + 0.5)
        draw.multiline_text((left, int(cy)), "\n".join(_wrap(draw, label, label_font, label_width - 8, 2)),
                            font=label_font, fill=COLORS["dark"], anchor="lm", spacing=1)
        x0 = plot_left + round(plot_width * low / maximum)
        x1 = plot_left + round(plot_width * high / maximum)
        line_y = int(cy)
        draw.line((x0, line_y, x1, line_y), fill=COLORS["teal"], width=max(5, round(8 * scale)))
        radius = max(4, round(7 * scale))
        draw.ellipse((x0 - radius, line_y - radius, x0 + radius, line_y + radius), fill=COLORS["blue"])
        draw.ellipse((x1 - radius, line_y - radius, x1 + radius, line_y + radius), fill=COLORS["teal"])
        value = _number_label(low, language, 3)
        if not math.isclose(low, high, abs_tol=1e-9):
            value += "–" + _number_label(high, language, 3)
        draw.text((min(x1 + 8, right - 6), line_y), value, font=value_font, fill=COLORS["dark"], anchor="lm")
    draw.text((plot_left + plot_width // 2, bottom - 3), "g", font=value_font, fill=COLORS["muted"], anchor="ms")


def _draw_food_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    gap = max(18, round(width * 0.018))
    top_bottom = top + round(height * 0.34)
    middle = (left + right) // 2
    balance = data["balance"]
    labels = [LANG_TEXT[language]["food_need"], LANG_TEXT[language]["food_reserve"], LANG_TEXT[language]["food_output"]]
    output_labels = [
        f"Продукция / потребность ×{_number_label(balance['calories']['stock'], language, 2)}" if language == "ru"
        else f"Output / need ×{_number_label(balance['calories']['stock'], language, 2)}",
        f"Продукция / потребность ×{_number_label(balance['protein']['stock'], language, 2)}" if language == "ru"
        else f"Output / need ×{_number_label(balance['protein']['stock'], language, 2)}",
    ]
    calorie_rows = [(labels[0], balance["calories"]["need"], ""),
                    (labels[1], balance["calories"]["reserve"], ""),
                    (output_labels[0], balance["calories"]["output"], "")]
    protein_rows = [(labels[0], balance["protein"]["need"], ""),
                    (labels[1], balance["protein"]["reserve"], ""),
                    (output_labels[1], balance["protein"]["output"], "")]
    _draw_hbars(
        draw, (left, top, middle - gap // 2, top_bottom), LANG_TEXT[language]["food_calories"],
        calorie_rows, language, "",
        max_value=2.6, label_ratio=0.43, value_digits=3, min_font=11,
    )
    _draw_hbars(
        draw, (middle + gap // 2, top, right, top_bottom), LANG_TEXT[language]["food_protein"],
        protein_rows, language, "",
        max_value=95, label_ratio=0.43, value_digits=1, min_font=11,
    )
    crops = sorted(data["crops"], key=lambda row: row["kcal"], reverse=True)
    crop_rows = [
        (row["label"], row["kcal"], f"{_number_label(row['area'], language, 0)} km²" if language == "en"
         else f"{_number_label(row['area'], language, 0)} км²")
        for row in crops
    ]
    total = _number_label(data["crop_total_kcal"], language, 0)
    area = _number_label(data["crop_total_area"], language, 0)
    crop_title = LANG_TEXT[language]["crop_total"] + (
        f" · {area} km²" if language == "en" else f" · {area} км²"
    )
    _draw_hbars(
        draw, (left, top_bottom + gap, right, bottom), crop_title,
        crop_rows, language, "",
        color=COLORS["green"], max_value=max(row["kcal"] for row in crops) * 1.55,
        label_ratio=0.47, value_digits=0, min_font=11, max_label_lines=2,
    )


def _draw_land_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    total = _number_label(data["total"], language, 0)
    title = LANG_TEXT[language]["land_area"] + (
        f" · total farmland {total} km²" if language == "en" else f" · всего сельхозугодий {total} км²"
    )
    rows = [
        (row["label"], row["area"], f"{_number_label(row['share'], language, 0)} %")
        for row in data["parts"]
    ]
    area_unit = "km²" if language == "en" else "км²"
    _draw_hbars(
        draw, (left, top, right, bottom), title, rows, language, area_unit,
        color=COLORS["green"], max_value=data["total"] * 1.05,
        label_ratio=0.49, value_digits=0, min_font=13,
    )
    scale = max(0.65, min((right - left) / 900.0, (bottom - top) / 480.0))
    subtotal = _number_label(data["agricultural_total"], language, 0)
    subtotal_share = _number_label(round(100 * data["agricultural_total"] / data["total"]), language, 0)
    note = (
        f"Agricultural-use subtotal: {subtotal} km² · {subtotal_share}%"
        if language == "en" else
        f"Сельхозиспользование: {subtotal} км² · {subtotal_share}%"
    )
    draw.text((left, top + round(34 * scale)), note, font=_font(max(11, round(14 * scale))),
              fill=COLORS["muted"])


def _draw_epidemic_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1100.0, height / 600.0))
    tick_font = _font(max(12, round(16 * scale)))
    body_font = _font(max(12, round(16 * scale)))
    heading_font = _font(max(14, round(20 * scale)), bold=True)
    plot_left = left + round(70 * scale)
    plot_right = left + round(width * 0.63)
    plot_top = top + round(52 * scale)
    plot_bottom = bottom - round(75 * scale)
    x_min, x_max = 1.0, 14.0
    y_min, y_max = 0.0, 1.0
    for percent in range(0, 101, 20):
        value = percent / 100.0
        y = plot_bottom - round(value * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(12 * scale), y), str(percent), font=tick_font,
                  fill=COLORS["muted"], anchor="rm")
    x_ticks = (1, 2, 4, 6, 8, 10, 12, 14)
    for tick in x_ticks:
        x = plot_left + round((tick - x_min) / (x_max - x_min) * (plot_right - plot_left))
        draw.line((x, plot_top, x, plot_bottom), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((x, plot_bottom + round(7 * scale)), str(tick), font=tick_font,
                  fill=COLORS["muted"], anchor="ma")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))

    def attack_rate(r0: float) -> float:
        if r0 <= 1.0:
            return 0.0
        low, high = 0.0, 1.0
        for _ in range(70):
            mid = (low + high) / 2.0
            if 1.0 - math.exp(-r0 * mid) - mid > 0:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    attack_points = []
    threshold_points = []
    for i in range(141):
        r0 = x_min + (x_max - x_min) * i / 140.0
        x = plot_left + round((r0 - x_min) / (x_max - x_min) * (plot_right - plot_left))
        ya = plot_bottom - round(attack_rate(r0) * (plot_bottom - plot_top))
        yh = plot_bottom - round(max(0.0, 1.0 - 1.0 / r0) * (plot_bottom - plot_top))
        attack_points.append((x, ya))
        threshold_points.append((x, yh))
    draw.line(attack_points, fill=COLORS["red"], width=max(3, round(4 * scale)), joint="curve")
    for i in range(0, len(threshold_points) - 1, 4):
        draw.line(threshold_points[i:i + 2], fill=COLORS["green"], width=max(3, round(4 * scale)))

    case_names = (
        ["Сезонный грипп", "Сценарий модели", "Оспа", "Корь"]
        if language == "ru" else
        ["Seasonal influenza", "Model case", "Smallpox", "Measles"]
    )
    for index, (r0, attack, threshold, name) in enumerate(
        zip(data["r0"], data["attack"], data["threshold"], case_names)
    ):
        x = plot_left + round((r0 - x_min) / (x_max - x_min) * (plot_right - plot_left))
        y_attack = plot_bottom - round(attack * (plot_bottom - plot_top))
        y_threshold = plot_bottom - round(threshold * (plot_bottom - plot_top))
        radius = max(5, round(7 * scale))
        draw.ellipse((x - radius, y_attack - radius, x + radius, y_attack + radius), fill=COLORS["red"])
        draw.ellipse((x - radius, y_threshold - radius, x + radius, y_threshold + radius), fill=COLORS["green"])

    draw.text(((plot_left + plot_right) // 2, bottom - round(11 * scale)),
              LANG_TEXT[language]["epidemic_r0"], font=tick_font, fill=COLORS["muted"], anchor="ms")
    draw.text((left + round(2 * scale), plot_top - round(24 * scale)),
              LANG_TEXT[language]["epidemic_attack"], font=tick_font, fill=COLORS["navy"])

    panel_left = plot_right + round(42 * scale)
    panel_right = right
    # Legend.
    legend_y = top + round(5 * scale)
    for y_off, color, label, dashed in (
        (0, COLORS["red"], LANG_TEXT[language]["epidemic_attack"], False),
        (round(33 * scale), COLORS["green"], LANG_TEXT[language]["epidemic_threshold"], True),
    ):
        y = legend_y + y_off
        if dashed:
            for x0 in range(panel_left, panel_left + round(42 * scale), round(12 * scale)):
                draw.line((x0, y, x0 + round(7 * scale), y), fill=color, width=max(2, round(3 * scale)))
        else:
            draw.line((panel_left, y, panel_left + round(42 * scale), y), fill=color, width=max(2, round(4 * scale)))
        draw.text((panel_left + round(52 * scale), y), label, font=body_font, fill=COLORS["dark"], anchor="lm")

    y_cursor = top + round(100 * scale)
    for r0, attack, name in zip(data["r0"], data["attack"], case_names):
        percent = round(100 * attack)
        cases_thousands = round(data["population"] * attack / 1000.0)
        text = f"R₀ = {_number_label(r0, language, 1)} · {name}"
        draw.text((panel_left, y_cursor), text, font=heading_font, fill=COLORS["navy"])
        y_cursor += round(26 * scale)
        draw.text((panel_left, y_cursor),
                  f"{percent}% · {_number_label(cases_thousands, language, 0)} " + ("thousand people" if language == "en" else "тыс. чел."),
                  font=body_font, fill=COLORS["muted"])
        y_cursor += round(48 * scale)
    note = (
        f"Closed population N = {_number_label(data['population'], language, 0)} · "
        f"4 sections: up to {_number_label(data['section_capacity'][0] / 1000, language, 1)}k people · "
        f"40 sections: up to {_number_label(data['section_capacity'][1] / 1000, language, 1)}k people"
        if language == "en" else
        f"Замкнутая популяция N = {_number_label(data['population'], language, 0)} · "
        f"4 секции: до {_number_label(data['section_capacity'][0] / 1000, language, 1)} тыс. чел. · "
        f"40 секций: до {_number_label(data['section_capacity'][1] / 1000, language, 1)} тыс. чел."
    )
    draw.multiline_text((panel_left, min(y_cursor + round(6 * scale), bottom - round(55 * scale))),
                        "\n".join(_wrap(draw, note, body_font, panel_right - panel_left, 3)),
                        font=body_font, fill=COLORS["green"], spacing=3)


def _draw_acoustics_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1100.0, height / 600.0))
    body_font = _font(max(12, round(15 * scale)))
    small_font = _font(max(11, round(13 * scale)))
    plot_left = left + round(width * 0.35)
    plot_right = right - round(width * 0.21)
    plot_top = top + round(45 * scale)
    plot_bottom = bottom - round(80 * scale)
    log_min, log_max = -3.0, math.log10(data["audible_high"])

    def x_pos(value: float) -> int:
        return plot_left + round((math.log10(value) - log_min) / (log_max - log_min) * (plot_right - plot_left))

    audible_x0 = x_pos(data["audible_low"])
    audible_x1 = x_pos(data["audible_high"])
    draw.rectangle((audible_x0, plot_top, audible_x1, plot_bottom), fill=(230, 241, 233))
    draw.text(((audible_x0 + audible_x1) // 2, plot_top + round(15 * scale)),
              LANG_TEXT[language]["sound_band"], font=small_font, fill=COLORS["green"], anchor="ma")
    ticks = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 20000.0)
    for value in ticks:
        x = x_pos(value)
        draw.line((x, plot_top, x, plot_bottom), fill=(215, 220, 224), width=max(1, round(scale)))
        if value in (10000.0, 20000.0):
            label = ("10k" if value == 10000 else "20k") if language == "en" else ("10 тыс." if value == 10000 else "20 тыс.")
        else:
            label = _number_label(value, language, 3)
        tick_anchor = "ra" if value == 10000.0 else ("la" if value == 20000.0 else "ma")
        draw.text((x, plot_bottom + round(7 * scale)), label, font=small_font,
                  fill=COLORS["muted"], anchor=tick_anchor)
    row_height = (plot_bottom - plot_top) / max(1, len(data["modes"]))
    for index, mode in enumerate(data["modes"]):
        cy = int(plot_top + row_height * (index + 0.5))
        draw.line((left + round(4 * scale), cy, right, cy), fill=(240, 242, 244), width=1)
        kind = mode["kind"]
        if kind == "long":
            label = f"{LANG_TEXT[language]['mode_long']}, {int(mode['order'])}"
            color = COLORS["blue"]
        elif kind == "transverse":
            label = LANG_TEXT[language]["mode_trans"]
            color = COLORS["sky"]
        else:
            label = LANG_TEXT[language]["mode_shell"]
            color = COLORS["gold"]
        _draw_wrapped(draw, (left + round(4 * scale), cy - round(10 * scale)), label,
                      body_font, round(width * 0.32), COLORS["dark"], max_lines=2)
        x = x_pos(mode["frequency"])
        draw.line((plot_left, cy, x, cy), fill=color, width=max(2, round(3 * scale)))
        radius = max(5, round(7 * scale))
        draw.ellipse((x - radius, cy - radius, x + radius, cy + radius), fill=color)
        frequency_unit, time_unit = ("Hz", "s") if language == "en" else ("Гц", "с")
        value_text = (
            f"{_number_label(mode['frequency'], language, 4)} {frequency_unit} · "
            f"{_number_label(mode['period'], language, 1 if mode['period'] < 10 else 0)} {time_unit}"
        )
        draw.text((plot_right + round(12 * scale), cy), value_text, font=small_font,
                  fill=COLORS["dark"], anchor="lm")
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.text(((plot_left + plot_right) // 2, bottom - round(8 * scale)),
              LANG_TEXT[language]["frequency"], font=small_font, fill=COLORS["muted"], anchor="ms")
    note = (
        "All five natural frequencies are below 20 Hz (infrasound)."
        if language == "en" else
        "Все пять собственных частот ниже 20 Гц (инфразвук)."
    )
    draw.text((left + round(4 * scale), top + round(5 * scale)), note,
              font=small_font, fill=COLORS["navy"])


def _draw_volatiles_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1100.0, height / 600.0))
    title_font = _font(max(14, round(20 * scale)), bold=True)
    body_font = _font(max(12, round(15 * scale)))
    small_font = _font(max(11, round(13 * scale)))
    plot_left = left + round(65 * scale)
    plot_right = left + round(width * 0.55)
    plot_top = top + round(78 * scale)
    footer_y = bottom - round(95 * scale)
    plot_bottom = footer_y - round(25 * scale)
    log_min, log_max = 0.0, 4.0

    def y_pos(value: float) -> int:
        return plot_bottom - round((math.log10(max(value, 1.0)) - log_min) / (log_max - log_min) * (plot_bottom - plot_top))

    ticks = (1.0, 10.0, 100.0, 1000.0, 10000.0)
    for value in ticks:
        y = y_pos(value)
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(12 * scale), y), _number_label(value, language, 0),
                  font=small_font, fill=COLORS["muted"], anchor="rm")
    y_station = y_pos(data["station_mass"])
    for x0 in range(plot_left, plot_right, round(18 * scale)):
        draw.line((x0, y_station, min(x0 + round(10 * scale), plot_right), y_station),
                  fill=COLORS["navy"], width=max(2, round(3 * scale)))
    draw.text((plot_left + round(6 * scale), y_station - round(10 * scale)),
              LANG_TEXT[language]["station_mass"], font=small_font, fill=COLORS["navy"], anchor="ls")
    colors = (COLORS["green"], COLORS["gold"], COLORS["red"], COLORS["gold"])
    rows = data["options"]
    gap = (plot_right - plot_left) / len(rows)
    bar_w = min(round(48 * scale), round(gap * 0.5))
    for index, row in enumerate(rows):
        cx = round(plot_left + gap * (index + 0.5))
        y = y_pos(row["raw"])
        draw.rectangle((cx - bar_w // 2, y, cx + bar_w // 2, plot_bottom), fill=colors[index])
        draw.text((cx, y - round(8 * scale)), _number_label(row["raw"], language, 2 if row["raw"] < 10 else 0),
                  font=body_font, fill=COLORS["dark"], anchor="ms")
        draw.text((cx, plot_bottom + round(10 * scale)), str(index + 1), font=body_font,
                  fill=COLORS["navy"], anchor="ma")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.text((plot_left, top + round(8 * scale)), LANG_TEXT[language]["raw_materials"],
              font=title_font, fill=COLORS["navy"])
    atmosphere_note = (
        f"Atmosphere total: {_number_label(data['atmosphere_total'], language, 2)} billion tons · water separate: {_number_label(data['water_stock'], language, 2)} billion tons"
        if language == "en" else
        f"Всего атмосферы: {_number_label(data['atmosphere_total'], language, 2)} млрд т · вода отдельно: {_number_label(data['water_stock'], language, 2)} млрд т"
    )
    draw.text((plot_left, top + round(38 * scale)), atmosphere_note,
              font=small_font, fill=COLORS["muted"])
    draw.text(((plot_left + plot_right) // 2, footer_y - round(2 * scale)),
              ("Feedstock option" if language == "en" else "Вариант источника"),
              font=small_font, fill=COLORS["muted"], anchor="ms")

    panel_left = left + round(width * 0.59)
    option_labels = (
        ["Oxygen · silicate regolith", "Water · CI chondrites", "Nitrogen · carbonaceous chondrites", "Nitrogen · cometary ice"]
        if language == "en" else
        ["Кислород · силикатный реголит", "Вода · CI-хондриты", "Азот · углистые хондриты", "Азот · кометные льды"]
    )
    y_cursor = top + round(5 * scale)
    for index, (row, label) in enumerate(zip(rows, option_labels)):
        draw.rectangle((panel_left, y_cursor + round(4 * scale), panel_left + round(18 * scale), y_cursor + round(28 * scale)),
                       fill=colors[index])
        draw.text((panel_left + round(30 * scale), y_cursor), f"{index + 1} · {label}",
                  font=title_font, fill=COLORS["dark"])
        need = _number_label(row["need"], language, 2)
        raw = _number_label(row["raw"], language, 2 if row["raw"] < 10 else 0)
        unit = "billion tons" if language == "en" else "млрд т"
        draw.text((panel_left + round(30 * scale), y_cursor + round(29 * scale)),
                  f"Need: {need} {unit} · feedstock: {raw} {unit}" if language == "en"
                  else f"Потребность: {need} {unit} · сырьё: {raw} {unit}",
                  font=body_font, fill=COLORS["muted"])
        if index == 3:
            comet_note = (
                f"≈{_number_label(data['comet_bodies'], language, 0)} bodies of 67P class"
                if language == "en" else
                f"≈{_number_label(data['comet_bodies'], language, 0)} тел класса 67P"
            )
            draw.text((panel_left + round(30 * scale), y_cursor + round(53 * scale)),
                      comet_note, font=small_font, fill=COLORS["muted"])
            y_cursor += round(98 * scale)
        else:
            y_cursor += round(80 * scale)
    alternative = data["options"][1]
    alt_note = (
        f"Water alternative: { _number_label(alternative['alternative_raw'], language, 2)} billion tons of CM chondrites at { _number_label(alternative['alternative_content'], language, 0)}%."
        if language == "en" else
        f"Альтернатива для воды: { _number_label(alternative['alternative_raw'], language, 2)} млрд т CM-хондритов при содержании { _number_label(alternative['alternative_content'], language, 0)}%."
    )
    draw.text((panel_left + round(30 * scale), min(y_cursor, footer_y - round(10 * scale))),
              alt_note, font=small_font, fill=COLORS["muted"])

    alt = data["alternative"]
    footer = (
        f"Alternative atmosphere: { _number_label(alt['pressure_kpa'], language, 0)} kPa, { _number_label(alt['oxygen_percent'], language, 0)}% O₂ → "
        f"{ _number_label(alt['atmosphere_mass'], language, 2)} billion tons atmosphere; { _number_label(alt['nitrogen_need'], language, 2)} billion tons N₂."
        if language == "en" else
        f"Альтернативная атмосфера: { _number_label(alt['pressure_kpa'], language, 0)} кПа, { _number_label(alt['oxygen_percent'], language, 0)}% O₂ → "
        f"{ _number_label(alt['atmosphere_mass'], language, 2)} млрд т атмосферы; { _number_label(alt['nitrogen_need'], language, 2)} млрд т N₂."
    )
    draw.rounded_rectangle((left, footer_y, right, bottom), radius=max(4, round(7 * scale)),
                           fill=(240, 244, 247), outline=(215, 220, 224), width=1)
    draw.text((left + round(12 * scale), footer_y + round((bottom - footer_y) / 2)), footer,
              font=small_font, fill=COLORS["navy"], anchor="lm")


def _draw_orbit_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    bodies: list[dict[str, Any]],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1100.0, height / 600.0))
    body_font = _font(max(12, round(15 * scale)))
    small_font = _font(max(11, round(13 * scale)))
    plot_left = left + round(width * 0.30)
    plot_right = left + round(width * 0.75)
    plot_top = top + round(68 * scale)
    plot_bottom = bottom - round(57 * scale)
    axis_max = 6.0

    def x_pos(value: float) -> int:
        return plot_left + round(value / axis_max * (plot_right - plot_left))

    legend_y = top + round(8 * scale)
    legend_items = (
        [("metal", "Metal", COLORS["red"]), ("water", "Water", COLORS["blue"]),
         ("nitrogen", "Nitrogen / silicates", COLORS["green"]), ("ice", "Ice", COLORS["sky"])]
        if language == "en" else
        [("metal", "Металлы", COLORS["red"]), ("water", "Вода", COLORS["blue"]),
         ("nitrogen", "Азот / силикаты", COLORS["green"]), ("ice", "Лёд", COLORS["sky"])]
    )
    legend_x = plot_left
    for _, label, color in legend_items:
        draw.line((legend_x, legend_y + round(8 * scale), legend_x + round(26 * scale), legend_y + round(8 * scale)),
                  fill=color, width=max(4, round(6 * scale)))
        draw.text((legend_x + round(34 * scale), legend_y + round(8 * scale)), label,
                  font=small_font, fill=COLORS["dark"], anchor="lm")
        legend_x += round(width * 0.19)

    rows_height = plot_bottom - plot_top
    row_height = rows_height / len(bodies)
    references = (
        [(1.0, "Earth / L1", -round(9 * scale)), (1.524, "Mars", round(12 * scale)),
         (5.2, "Jupiter", -round(9 * scale))]
        if language == "en" else
        [(1.0, "Земля / L1", -round(9 * scale)), (1.524, "Марс", round(12 * scale)),
         (5.2, "Юпитер", -round(9 * scale))]
    )
    for value, label, label_offset in references:
        x = x_pos(value)
        for y0 in range(plot_top, plot_bottom, round(14 * scale)):
            draw.line((x, y0, x, min(y0 + round(7 * scale), plot_bottom)),
                      fill=(151, 158, 166), width=max(1, round(2 * scale)))
        draw.text((x, plot_top + label_offset), label, font=small_font,
                  fill=COLORS["muted"], anchor="ms")
    palette = {"metal": COLORS["red"], "water": COLORS["blue"], "nitrogen": COLORS["green"], "ice": COLORS["sky"]}
    for index, body in enumerate(bodies):
        cy = int(plot_top + row_height * (index + 0.5))
        draw.line((left, cy + int(row_height / 2), right, cy + int(row_height / 2)),
                  fill=(238, 240, 242), width=1)
        label_lines = _wrap(draw, body["label"], body_font, round(width * 0.28), 2)
        draw.multiline_text((left + round(3 * scale), cy), "\n".join(label_lines), font=body_font,
                            fill=COLORS["dark"], anchor="lm", spacing=1)
        x_q = x_pos(body["perihelion"])
        x_Q = x_pos(body["aphelion"])
        x_a = x_pos(body["a"])
        color = palette.get(body["role"], COLORS["blue"])
        draw.line((x_q, cy, x_Q, cy), fill=color, width=max(5, round(8 * scale)))
        radius = max(5, round(7 * scale))
        draw.ellipse((x_q - radius, cy - radius, x_q + radius, cy + radius), fill=color)
        draw.ellipse((x_Q - radius, cy - radius, x_Q + radius, cy + radius), fill=color)
        draw.ellipse((x_a - radius, cy - radius, x_a + radius, cy + radius), fill=COLORS["white"], outline=COLORS["navy"], width=max(2, round(3 * scale)))
        summary = (
            f"q {_number_label(body['perihelion'], language, 2)} · a {_number_label(body['a'], language, 2)} · "
            f"Q {_number_label(body['aphelion'], language, 2)} AU\n"
            f"e {_number_label(body['e'], language, 3)} · i {_number_label(body['inclination'], language, 1)}°"
        )
        if body["period"] is not None:
            summary += f" · P {_number_label(body['period'], language, 1)} y" if language == "en" else f" · P {_number_label(body['period'], language, 1)} г"
        draw.multiline_text((plot_right + round(15 * scale), cy), summary, font=small_font,
                            fill=COLORS["dark"], anchor="lm", spacing=2)
    for tick in range(0, 7):
        x = x_pos(float(tick))
        draw.line((x, plot_bottom, x, plot_bottom + round(5 * scale)), fill=COLORS["gray"], width=1)
        draw.text((x, plot_bottom + round(10 * scale)), str(tick), font=small_font,
                  fill=COLORS["muted"], anchor="ma")
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.text(((plot_left + plot_right) // 2, bottom - round(7 * scale)), "AU",
              font=small_font, fill=COLORS["muted"], anchor="ms")


def _draw_quarantine_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1300.0, height / 720.0))
    heading_font = _font(max(13, round(17 * scale)), bold=True)
    body_font = _font(max(12, round(15 * scale)))
    small_font = _font(max(11, round(13 * scale)))
    label_width = round(width * 0.17)
    stage_gap = round(width * 0.025)
    stage_left = left + label_width
    stage_right = right - round(width * 0.01)
    stage_width = (stage_right - stage_left - 2 * stage_gap) / 3
    header_y = top + round(5 * scale)
    stage_headers = [
        LANG_TEXT[language]["quarantine_stage_1"],
        LANG_TEXT[language]["quarantine_stage_2"],
        LANG_TEXT[language]["quarantine_stage_3"],
    ]
    stage_colors = [COLORS["blue"], COLORS["gold"], COLORS["green"]]
    for index, (stage, color) in enumerate(zip(stage_headers, stage_colors)):
        x0 = round(stage_left + index * (stage_width + stage_gap))
        draw.text((x0, header_y), stage, font=heading_font, fill=color)
    flow_names = data["flows"]
    colors = [COLORS["blue"], COLORS["green"], COLORS["gold"], COLORS["sky"]]
    stage_copy = (
        [
            ["Exam + lab tests", "Quarantine assessment", "Vacuum opening + inspection", "Vacuum venting + filter"],
            ["40-day isolation", "Biological isolator + first crop", "25 kGy gamma or 200 °C heat", "Separate ventilation + filtration / UV"],
            ["Release after negative tests", "Transfer to biosphere", "Control sowing", "Test before utility supply"],
        ] if language == "en" else [
            ["Осмотр + лабораторные тесты", "Карантинная оценка", "Открытие в вакууме + осмотр", "Вакуумная дегазация + фильтр"],
            ["Изоляция 40 дней", "Биоизолятор + первый урожай", "25 кГр гамма-излучения или 200 °C", "Отдельная вентиляция + фильтрация / УФ"],
            ["Допуск после отрицательных тестов", "Перевод в биосферу", "Контрольный посев", "Проверка перед подачей в сеть"],
        ]
    )
    footer_height = round(92 * scale)
    rows_top = top + round(52 * scale)
    rows_bottom = bottom - footer_height - round(12 * scale)
    row_height = (rows_bottom - rows_top) / len(flow_names)
    box_h = min(round(78 * scale), round(row_height * 0.62))
    for row_index, flow_name in enumerate(flow_names):
        cy = int(rows_top + row_height * (row_index + 0.5))
        color = colors[row_index % len(colors)]
        _draw_wrapped(draw, (left + round(2 * scale), cy - round(15 * scale)), flow_name,
                      heading_font, label_width - round(10 * scale), COLORS["navy"], max_lines=2)
        for stage_index in range(3):
            x0 = round(stage_left + stage_index * (stage_width + stage_gap))
            x1 = round(x0 + stage_width)
            y0, y1 = cy - box_h // 2, cy + box_h // 2
            draw.rounded_rectangle((x0, y0, x1, y1), radius=max(4, round(8 * scale)),
                                   fill=(250, 251, 252), outline=color, width=max(2, round(2 * scale)))
            _draw_wrapped(draw, (x0 + round(9 * scale), y0 + round(8 * scale)),
                          stage_copy[stage_index][row_index], body_font, int(stage_width - round(18 * scale)),
                          COLORS["dark"], max_lines=3)
            if stage_index < 2:
                ax0 = x1 + round(3 * scale)
                ax1 = round(stage_left + (stage_index + 1) * (stage_width + stage_gap)) - round(4 * scale)
                draw.line((ax0, cy, ax1, cy), fill=color, width=max(2, round(3 * scale)))
                draw.polygon(((ax1, cy), (ax1 - round(9 * scale), cy - round(6 * scale)),
                              (ax1 - round(9 * scale), cy + round(6 * scale))), fill=color)
    footer_y = bottom - footer_height
    draw.rounded_rectangle((left, footer_y, right, bottom), radius=max(4, round(8 * scale)),
                           fill=(240, 244, 247), outline=(215, 220, 224), width=1)
    flow_rate = round(data["annual_flow"] / 365.0)
    footer_lines = (
        [
            f"Flow: {_number_label(data['annual_flow'], language, 0)} people/year · "
            f"{_number_label(flow_rate, language, 0)} people/day · {_number_label(data['hold_days'], language, 0)} days · "
            f"{_number_label(data['places'], language, 0)} concurrent places · "
            f"{_number_label(data['cycles'], language, 2)} cycles/year",
            f"Isolation block: {_number_label(data['block_area'], language, 0)} m² · {_number_label(data['block_boxes'], language, 0)} boxes",
            f"Shared clean channel Ø {_number_label(data['channel_diameter'], language, 1)} m · sealed bulkhead · separate ventilation to the inhabited zone",
        ] if language == "en" else [
            f"Расчёт потока {_number_label(data['annual_flow'], language, 0)} человек/год · "
            f"{_number_label(flow_rate, language, 0)} в сутки · {_number_label(data['hold_days'], language, 0)} суток · "
            f"{_number_label(data['places'], language, 0)} место единовременно · "
            f"{_number_label(data['cycles'], language, 2)} цикла/год",
            f"Карантинный блок: {_number_label(data['block_area'], language, 0)} м² · {_number_label(data['block_boxes'], language, 0)} боксов",
            f"Общий чистый канал Ø {_number_label(data['channel_diameter'], language, 1)} м · гермопереборка · отдельная вентиляция к жилой зоне",
        ]
    )
    draw.multiline_text((left + round(16 * scale), footer_y + round(11 * scale)),
                        "\n".join(footer_lines), font=small_font, fill=COLORS["navy"], spacing=round(7 * scale))


def _draw_panel_choice_figure(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    data: dict[str, Any],
    language: str,
) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    scale = max(0.65, min(width / 1250.0, height / 700.0))
    tick_font = _font(max(11, round(13 * scale)))
    body_font = _font(max(12, round(15 * scale)))
    title_font = _font(max(14, round(19 * scale)), bold=True)
    footer_height = round(94 * scale)
    plot_left = left + round(width * 0.09)
    plot_right = left + round(width * 0.68)
    plot_top = top + round(62 * scale)
    plot_bottom = bottom - footer_height - round(58 * scale)
    w_min, w_max = data["width_min"], data["width_max"]
    seam_max, mass_max = 200.0, 200.0
    circumference = 2.0 * math.pi * data["cylinder_radius"]

    def x_pos(panel_width: float) -> int:
        return plot_left + round((panel_width - w_min) / (w_max - w_min) * (plot_right - plot_left))

    def y_seam(value: float) -> int:
        return plot_bottom - round(value / seam_max * (plot_bottom - plot_top))

    def y_mass(value: float) -> int:
        return plot_bottom - round(value / mass_max * (plot_bottom - plot_top))

    # The 40–60 m range is the documented working window.
    draw.rectangle((x_pos(40), plot_top, x_pos(60), plot_bottom), fill=(233, 243, 236))
    for tick in range(0, 201, 50):
        y = y_seam(float(tick))
        draw.line((plot_left, y, plot_right, y), fill=COLORS["light"], width=max(1, round(scale)))
        draw.text((plot_left - round(10 * scale), y), str(tick), font=tick_font,
                  fill=COLORS["muted"], anchor="rm")
        draw.text((plot_right + round(10 * scale), y), str(tick), font=tick_font,
                  fill=COLORS["muted"], anchor="lm")
    for tick in range(10, 121, 10):
        x = x_pos(float(tick))
        if tick in (10, 20, 40, 50, 60, 80, 100, 120):
            draw.line((x, plot_bottom, x, plot_bottom + round(5 * scale)), fill=COLORS["gray"], width=1)
            draw.text((x, plot_bottom + round(9 * scale)), str(tick), font=tick_font,
                      fill=COLORS["muted"], anchor="ma")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_right, plot_top, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=COLORS["gray"], width=max(1, round(2 * scale)))

    seam_points = []
    mass_points = []
    for step in range(111):
        panel_width = w_min + (w_max - w_min) * step / 110.0
        seam_km = (1.0 + 1.0 / data["aspect_ratio"]) * circumference * data["cylinder_length"] / panel_width / 1_000_000.0
        mass_kt = data["accepted_mass"] * (panel_width / data["accepted_width"]) ** 2 / 1000.0
        seam_points.append((x_pos(panel_width), y_seam(seam_km)))
        mass_points.append((x_pos(panel_width), y_mass(mass_kt)))
    draw.line(seam_points, fill=COLORS["blue"], width=max(3, round(4 * scale)), joint="curve")
    draw.line(mass_points, fill=COLORS["teal"], width=max(3, round(4 * scale)), joint="curve")

    accepted_x = x_pos(data["accepted_width"])
    for y0 in range(plot_top, plot_bottom, round(16 * scale)):
        draw.line((accepted_x, y0, accepted_x, min(y0 + round(8 * scale), plot_bottom)),
                  fill=COLORS["navy"], width=max(2, round(2 * scale)))
    seam_accepted = (
        (1.0 + 1.0 / data["aspect_ratio"]) * circumference * data["cylinder_length"]
        / data["accepted_width"] / 1_000_000.0
    )
    mass_accepted = data["accepted_mass"] / 1000.0
    radius = max(5, round(7 * scale))
    seam_point = (accepted_x - round(4 * scale), y_seam(seam_accepted))
    mass_point = (accepted_x + round(4 * scale), y_mass(mass_accepted))
    draw.rectangle((seam_point[0] - radius, seam_point[1] - radius,
                    seam_point[0] + radius, seam_point[1] + radius),
                   fill=COLORS["blue"], outline=COLORS["white"], width=2)
    draw.ellipse((mass_point[0] - radius, mass_point[1] - radius,
                  mass_point[0] + radius, mass_point[1] + radius),
                 fill=COLORS["teal"], outline=COLORS["white"], width=2)

    draw.text((plot_left, top + round(4 * scale)),
              "Weld seams · thousand km" if language == "en" else "Сварные швы · тыс. км",
              font=title_font, fill=COLORS["blue"])
    draw.text((plot_right, top + round(4 * scale)),
              "Panel mass · thousand tons" if language == "en" else "Масса панели · тыс. т",
              font=title_font, fill=COLORS["teal"], anchor="ra")
    draw.text(((plot_left + plot_right) // 2, plot_bottom + round(42 * scale)),
              "Panel width, m" if language == "en" else "Ширина панели, м",
              font=tick_font, fill=COLORS["muted"], anchor="ms")

    note_left = plot_right + round(width * 0.045)
    note_top = top + round(70 * scale)
    items = (
        [
            (f"{_number_label(data['accepted_width'], language, 0)} × {_number_label(data['accepted_length'], language, 0)} m", "accepted panel"),
            (f"{_number_label(data['accepted_mass'], language, 0)} tons", "mass"),
            (f"{_number_label(data['accepted_seams'], language, 1)} thousand km", "weld seams / cylinder"),
            (f"{_number_label(data['camber_50'], language, 0)} mm", "camber at 50 m"),
            (f"{_number_label(data['camber_100'], language, 0)} mm", "camber at 100 m"),
            (f"{_number_label(data['fill_time_50'], language, 0)} min", "form filling"),
            (f"{_number_label(data['panel_count'], language, 0)}", "panels per cylinder"),
        ] if language == "en" else [
            (f"{_number_label(data['accepted_width'], language, 0)} × {_number_label(data['accepted_length'], language, 0)} м", "принятая панель"),
            (f"{_number_label(data['accepted_mass'], language, 0)} т", "масса"),
            (f"{_number_label(data['accepted_seams'], language, 1)} тыс. км", "швов на цилиндр"),
            (f"{_number_label(data['camber_50'], language, 0)} мм", "прогиб при 50 м"),
            (f"{_number_label(data['camber_100'], language, 0)} мм", "прогиб при 100 м"),
            (f"{_number_label(data['fill_time_50'], language, 0)} мин", "заполнение формы"),
            (f"{_number_label(data['panel_count'], language, 0)}", "панелей на цилиндр"),
        ]
    )
    cursor_y = note_top
    for value, label in items:
        draw.text((note_left, cursor_y), value, font=title_font, fill=COLORS["navy"])
        cursor_y += round(26 * scale)
        draw.text((note_left, cursor_y), label, font=body_font, fill=COLORS["muted"])
        cursor_y += round(43 * scale)
    window = (
        "Working width window: 40–60 m; seam length ∝ 1/width, panel mass ∝ width²."
        if language == "en" else
        "Рабочее окно: 40–60 м; длина швов ∝ 1/ширине, масса панели ∝ ширине²."
    )
    footer_y = bottom - footer_height
    draw.rounded_rectangle((left, footer_y, right, bottom), radius=max(4, round(8 * scale)),
                           fill=(240, 244, 247), outline=(215, 220, 224), width=1)
    draw.text((left + round(14 * scale), footer_y + round(17 * scale)), window,
              font=body_font, fill=COLORS["navy"])
    draw.text((left + round(14 * scale), footer_y + round(53 * scale)),
              f"Cylinder: R = {_number_label(data['cylinder_radius'] / 1000, language, 0)} km · L = {_number_label(data['cylinder_length'] / 1000, language, 0)} km"
              if language == "en" else
              f"Цилиндр: R = {_number_label(data['cylinder_radius'] / 1000, language, 0)} км · L = {_number_label(data['cylinder_length'] / 1000, language, 0)} км",
              font=tick_font, fill=COLORS["muted"])


def _figure_size(language: str, figure: str) -> tuple[int, int]:






    path = ASSET_DIRS[language] / f"{figure}.png"
    if not path.is_file():
        raise FileNotFoundError(f"expected existing image for dimensions: {path.relative_to(ROOT)}")
    with Image.open(path) as image:
        return image.size


def generate_all(selected: list[str]) -> dict[str, dict[str, Image.Image]]:
    catalogs = {lang: TableCatalog(path) for lang, path in DOCS.items()}
    data = {lang: extract_edition_data(lang, catalog) for lang, catalog in catalogs.items()}
    _validate_bilingual(data)
    generated: dict[str, dict[str, Image.Image]] = {"ru": {}, "en": {}}
    for language in ("ru", "en"):
        for figure in selected:
            size = _figure_size(language, figure)
            generated[language][figure] = render_figure(figure, language, data[language], size)
    return generated


def _numeric_signature(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 6)
    if isinstance(value, list):
        return [_numeric_signature(item) for item in value]
    if isinstance(value, tuple):
        return [_numeric_signature(item) for item in value]
    if isinstance(value, dict):
        return {key: _numeric_signature(value[key]) for key in sorted(value)}
    return None


def _validate_bilingual(data: dict[str, dict[str, Any]]) -> None:
    for figure in FIGURES:
        ru_signature = _numeric_signature(data["ru"][figure])
        en_signature = _numeric_signature(data["en"][figure])
        if ru_signature != en_signature:
            raise ValueError(
                f"RU/EN numeric table data differ for {figure}; refusing to generate inconsistent images.\n"
                f"RU={ru_signature}\nEN={en_signature}"
            )


def save_preview(generated: dict[str, dict[str, Image.Image]], output_dir: Path) -> None:
    for language, images in generated.items():
        folder = output_dir / language
        folder.mkdir(parents=True, exist_ok=True)
        for stem, image in images.items():
            path = folder / f"{stem}.png"
            image.save(path, format="PNG", optimize=True)
            print(f"preview: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def _image_bytes(image: Image.Image) -> bytes:
    stream = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024)
    image.save(stream, format="PNG", optimize=True)
    stream.seek(0)
    return stream.read()


def _patch_docx_media(language: str, new_assets: dict[str, bytes], source_hashes: dict[str, str]) -> Path:
    """Create a staged DOCX with the selected embedded PNGs replaced by hash identity."""
    source_doc = DOCS[language]
    selected_hashes = [source_hashes[stem] for stem in new_assets]
    if len(set(selected_hashes)) != len(selected_hashes):
        raise ValueError(f"{source_doc.name}: selected site images do not have unique source hashes")
    replacements_by_hash = {
        source_hashes[stem]: new_assets[stem]
        for stem in new_assets
    }
    matched: Counter[str] = Counter()
    fd, temp_name = tempfile.mkstemp(prefix=f"{source_doc.stem}-", suffix=".docx", dir=source_doc.parent)
    os.close(fd)
    staged_doc = Path(temp_name)
    try:
        with zipfile.ZipFile(source_doc, "r") as source_zip, zipfile.ZipFile(staged_doc, "w") as target_zip:
            for info in source_zip.infolist():
                payload = source_zip.read(info.filename)
                if info.filename.startswith("word/media/") and info.filename.lower().endswith(".png"):
                    digest = hashlib.sha256(payload).hexdigest()
                    if digest in replacements_by_hash:
                        payload = replacements_by_hash[digest]
                        matched[digest] += 1
                target_zip.writestr(info, payload)
        missing = [stem for stem, digest in source_hashes.items()
                   if stem in new_assets and matched[digest] != 1]
        if missing:
            raise ValueError(
                f"{source_doc.name}: could not uniquely match embedded source PNGs for {missing}; "
                "the document and site assets may be out of sync"
            )
        return staged_doc
    except Exception:
        staged_doc.unlink(missing_ok=True)
        raise


def apply_changes(generated: dict[str, dict[str, Image.Image]], sync_docx: bool) -> None:
    """Stage the bilingual asset/DOCX update, then atomically replace selected files."""
    staged_assets: dict[str, dict[str, Path]] = {"ru": {}, "en": {}}
    staged_docs: dict[str, Path] = {}
    source_hashes: dict[str, dict[str, str]] = {"ru": {}, "en": {}}
    try:
        for language, images in generated.items():
            for stem, image in images.items():
                source_path = ASSET_DIRS[language] / f"{stem}.png"
                if not source_path.is_file():
                    raise FileNotFoundError(source_path)
                source_hashes[language][stem] = hashlib.sha256(source_path.read_bytes()).hexdigest()
                fd, temp_name = tempfile.mkstemp(prefix=f"{stem}-", suffix=".png", dir=ASSET_DIRS[language])
                os.close(fd)
                temp_path = Path(temp_name)
                image.save(temp_path, format="PNG", optimize=True)
                with Image.open(temp_path) as check:
                    check.load()
                    if check.size != image.size:
                        raise ValueError(f"staged image dimension mismatch: {temp_path}")
                staged_assets[language][stem] = temp_path

        if sync_docx:
            for language, images in generated.items():
                payloads = {stem: _image_bytes(image) for stem, image in images.items()}
                staged_docs[language] = _patch_docx_media(language, payloads, source_hashes[language])

        for language, files in staged_assets.items():
            for stem, temp_path in files.items():
                os.replace(temp_path, ASSET_DIRS[language] / f"{stem}.png")
        for language, temp_path in staged_docs.items():
            os.replace(temp_path, DOCS[language])

        print("Updated Edition 8 PNG charts in site/assets/fig_ru and fig_en.")
        if sync_docx:
            print("Updated matching embedded chart images in both combined Edition 8 DOCX files.")
        subprocess.run([sys.executable, str(ROOT / "site" / "build_pages.py")], cwd=ROOT, check=True)
        print("Rebuilt all standalone RU/EN site pages.")
    finally:
        for files in staged_assets.values():
            for path in files.values():
                path.unlink(missing_ok=True)
        for path in staged_docs.values():
            path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="replace selected chart images in both site asset sets and rebuild standalone HTML",
    )
    parser.add_argument(
        "--sync-docx",
        action="store_true",
        help="also replace matching embedded images in both combined DOCX files (requires --apply)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PREVIEW_DIR,
        help=f"preview output directory (default: {PREVIEW_DIR.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--figures",
        nargs="+",
        choices=FIGURES,
        default=list(FIGURES),
        help="subset of selected figure stems to generate",
    )
    args = parser.parse_args()
    if args.sync_docx and not args.apply:
        parser.error("--sync-docx requires --apply")
    return args


def main() -> int:
    args = parse_args()
    try:
        generated = generate_all(args.figures)
        if args.apply:
            apply_changes(generated, sync_docx=args.sync_docx)
        else:
            save_preview(generated, args.output_dir)
            print(
                f"Generated {sum(len(items) for items in generated.values())} preview charts. "
                "No site assets or DOCX files were changed; use --apply to publish them."
            )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
