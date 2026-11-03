#!/usr/bin/env python3
"""Optional generator of generic, non-official placeholder artwork.

This is not a logo-recovery tool and is not part of the website build. It does
not write anything unless --write-placeholders is supplied, and it never
replaces an existing file unless --force is also supplied.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size: int, bold: bool = True):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except OSError:
        return ImageFont.load_default()


def rounded(color, radius: int = 56) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=radius, fill=color)
    return img


def gradient(c1, c2) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    grad = Image.new("RGB", (SIZE, SIZE))
    px = grad.load()
    for y in range(SIZE):
        for x in range(SIZE):
            t = (x + y) / (2 * SIZE)
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=56, fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def centered_text(draw: ImageDraw.ImageDraw, text: str, size: int, y: int,
                  fill=(255, 255, 255, 255), bold=True) -> None:
    selected_font = font(size, bold)
    box = draw.textbbox((0, 0), text, font=selected_font)
    draw.text(((SIZE - (box[2] - box[0])) / 2 - box[0], y), text,
              font=selected_font, fill=fill)


def envelope(draw: ImageDraw.ImageDraw, color=(255, 255, 255, 255)) -> None:
    x0, y0, x1, y1 = 48, 78, 208, 178
    draw.rounded_rectangle((x0, y0, x1, y1), radius=14, outline=color, width=10)
    draw.line((x0 + 8, y0 + 10, SIZE / 2, y0 + 52), fill=color, width=10)
    draw.line((x1 - 8, y0 + 10, SIZE / 2, y0 + 52), fill=color, width=10)


def heart(draw: ImageDraw.ImageDraw, cy: int = 104, scale: float = 1.0,
          color=(255, 255, 255, 255)) -> None:
    r = 34 * scale
    cx = SIZE / 2
    draw.ellipse((cx - 2 * r, cy - r, cx, cy + r), fill=color)
    draw.ellipse((cx, cy - r, cx + 2 * r, cy + r), fill=color)
    draw.polygon([(cx - 2 * r, cy + 2), (cx + 2 * r, cy + 2), (cx, cy + 3.1 * r)], fill=color)


def building(draw: ImageDraw.ImageDraw, color=(255, 255, 255, 255)) -> None:
    draw.rectangle((72, 92, 184, 196), fill=color)
    draw.polygon([(64, 92), (192, 92), (128, 52)], fill=color)
    for col in (96, 124, 152):
        draw.rectangle((col, 112, col + 16, 132), fill=(31, 95, 169, 255))
        draw.rectangle((col, 148, col + 16, 168), fill=(31, 95, 169, 255))


def save(img: Image.Image, path: Path, force: bool) -> bool:
    if path.exists() and not force:
        print(f"  пропуск существующего файла: {path.name} (для перезаписи нужен --force)")
        return False
    img.save(path, "PNG", optimize=True)
    print(f"  {path.name}  {path.stat().st_size / 1024:.1f} КБ")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Create generic non-official placeholder icons.")
    parser.add_argument(
        "--out", type=Path,
        default=Path(__file__).resolve().parent.parent / "site" / "icons",
        help="output directory",
    )
    parser.add_argument(
        "--write-placeholders", action="store_true",
        help="explicitly allow creation of generic placeholder artwork",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="overwrite existing files (requires --write-placeholders)",
    )
    args = parser.parse_args()

    if args.force and not args.write_placeholders:
        parser.error("--force requires --write-placeholders")
    if not args.write_placeholders:
        print("Ничего не изменено. Для явного создания заглушек укажите --write-placeholders.")
        return 0

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    print(f"Создание неофициальных заглушек в {out}")
    saved = 0

    img = rounded((0, 119, 255, 255))
    centered_text(ImageDraw.Draw(img), "VK", 118, 58)
    saved += save(img, out / "Icon-Color.png", args.force)

    img = gradient((108, 92, 231), (0, 194, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((56, 72, 200, 168), radius=28, outline=(255, 255, 255, 255), width=10)
    draw.polygon([(86, 168), (86, 206), (128, 168)], fill=(255, 255, 255, 255))
    saved += save(img, out / "Max-logo-2025.png", args.force)

    img = rounded((143, 126, 214, 255))
    envelope(ImageDraw.Draw(img))
    saved += save(img, out / "1200x630wa.png", args.force)

    img = rounded((255, 107, 107, 255))
    draw = ImageDraw.Draw(img)
    heart(draw, cy=100, scale=0.80)
    centered_text(draw, "ДОБРО", 34, 186)
    saved += save(img, out / "6v-QBl8-L6mgk.png", args.force)

    img = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    centered_text(ImageDraw.Draw(img), "Я", 168, 24, fill=(252, 63, 29, 255))
    saved += save(img, out / "yandex-logo-rus.png", args.force)

    img = rounded((31, 95, 169, 255))
    building(ImageDraw.Draw(img))
    centered_text(ImageDraw.Draw(img), "МИНСТРОЙ", 26, 204)
    saved += save(img, out / "Minstroy-RF.png", args.force)

    print(f"Готово: записано {saved} неофициальных заглушек.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
