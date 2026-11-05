#!/usr/bin/env python3
"""Verify the generated 14-page site and its language-specific project logos."""
from __future__ import annotations

import base64
from collections import Counter
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

from PIL import Image

from build_pages import LOGO_ASSETS, LOGO_MAX_WIDTH, PAGES

SITE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SITE_ROOT.parent
OUTPUT_DIRS = {
    "site/ru": SITE_ROOT / "ru",
    "site/en": SITE_ROOT / "en",
    "ru": REPO_ROOT / "ru",
    "en": REPO_ROOT / "en",
}


class LogoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.logos: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attributes = {key: value or "" for key, value in attrs}
        if "data-site-logo" in attributes:
            self.logos.append(attributes)


def source_pixel_variants(language: str) -> list[tuple[tuple[int, int], bytes]]:
    source_path = SITE_ROOT / LOGO_ASSETS[language]
    if not source_path.is_file():
        raise ValueError(f"missing {language} logo asset: {source_path.relative_to(REPO_ROOT)}")

    with Image.open(source_path) as source:
        if source.format != "PNG":
            raise ValueError(f"{source_path.name} is not a PNG")
        rgba = source.convert("RGBA")
        variants = [(rgba.size, rgba.tobytes())]
        if rgba.width > LOGO_MAX_WIDTH:
            resized = rgba.resize(
                (LOGO_MAX_WIDTH, round(rgba.height * LOGO_MAX_WIDTH / rgba.width)),
                Image.Resampling.LANCZOS,
            )
            variants.append((resized.size, resized.tobytes()))
        return variants


def check_transparent_english_source() -> list[str]:
    path = SITE_ROOT / LOGO_ASSETS["en"]
    errors: list[str] = []
    try:
        with Image.open(path) as image:
            if image.mode != "RGBA" or image.size != (1600, 1600):
                errors.append(f"English logo source must remain RGBA 1600×1600; found {image.mode} {image.size}")
            alpha = image.getchannel("A")
            if alpha.getextrema() != (0, 255):
                errors.append("English logo source must contain both transparent and opaque pixels")
            corners = ((0, 0), (1599, 0), (0, 1599), (1599, 1599))
            if any(alpha.getpixel(point) != 0 for point in corners):
                errors.append("English logo source must have a transparent background at all four corners")
    except Exception as exc:  # report the asset problem as a validation failure
        errors.append(f"cannot read English logo source {path}: {exc}")
    return errors


def embedded_logo_matches(language: str, src: str, cache: set[tuple[str, str]]) -> str | None:
    prefix = "data:image/png;base64,"
    if not src.startswith(prefix):
        return "logo is not embedded as a PNG data URI"
    payload = src[len(prefix):]
    cache_key = (language, payload)
    if cache_key in cache:
        return None
    try:
        blob = base64.b64decode(payload, validate=True)
        with Image.open(BytesIO(blob)) as embedded:
            if embedded.format != "PNG":
                return "embedded logo is not a PNG"
            embedded.load()
            actual = embedded.convert("RGBA")
            actual_pixels = (actual.size, actual.tobytes())
        if actual_pixels not in source_pixel_variants(language):
            return f"embedded logo pixels do not match the {language} source asset"
    except Exception as exc:
        return f"cannot decode embedded logo: {exc}"
    cache.add(cache_key)
    return None


def main() -> int:
    errors = check_transparent_english_source()
    expected_pages = {
        language: {page["output"] for page in PAGES if page["lang"] == language}
        for language in ("ru", "en")
    }
    if any(len(names) != 7 for names in expected_pages.values()) or len(PAGES) != 14:
        errors.append("site builder must define exactly seven pages per language (14 total)")

    embedded_cache: set[tuple[str, str]] = set()
    checked_files = 0
    for folder_label, folder in OUTPUT_DIRS.items():
        language = folder_label.rsplit("/", 1)[-1]
        expected_names = expected_pages[language]
        actual_names = {
            path.name
            for path in folder.glob("*.html")
            if not (language == "ru" and path.name == "title.html")  # retained Russian legacy page
        }
        if actual_names != expected_names:
            missing = sorted(expected_names - actual_names)
            extra = sorted(actual_names - expected_names)
            errors.append(f"{folder_label}: current page set mismatch; missing={missing}, extra={extra}")

        for page in PAGES:
            if page["lang"] != language:
                continue
            path = folder / page["output"]
            if not path.is_file():
                continue
            checked_files += 1
            try:
                html = path.read_text(encoding="utf-8")
            except Exception as exc:
                errors.append(f"{path.relative_to(REPO_ROOT)}: cannot read HTML: {exc}")
                continue

            parser = LogoParser()
            parser.feed(html)
            roles = Counter(logo.get("data-site-logo", "") for logo in parser.logos)
            expected_roles = Counter({"nav": 1})
            if page["slug"] in {"index", "index-en"}:
                expected_roles["hero"] = 1
            if roles != expected_roles:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: expected logo roles {dict(expected_roles)}, found {dict(roles)}"
                )

            for logo in parser.logos:
                role = logo.get("data-site-logo", "unknown")
                if logo.get("data-logo-language") != language:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: {role} logo is not localized for {language}"
                    )
                mismatch = embedded_logo_matches(language, logo.get("src", ""), embedded_cache)
                if mismatch:
                    errors.append(f"{path.relative_to(REPO_ROOT)}: {role} logo: {mismatch}")

    for language, names in expected_pages.items():
        for name in names:
            generated = OUTPUT_DIRS[f"site/{language}"] / name
            published = OUTPUT_DIRS[language] / name
            if generated.is_file() and published.is_file():
                if generated.read_bytes() != published.read_bytes():
                    errors.append(f"{published.relative_to(REPO_ROOT)} is out of sync with {generated.relative_to(REPO_ROOT)}")

    if errors:
        for error in errors:
            print("FAIL:", error)
        print(f"Result: FAIL ({len(errors)} errors)")
        return 1

    print(
        f"PASS: {checked_files} generated/published HTML files; 14 current pages; "
        "language-matched nav and homepage logos; transparent English logo source."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
