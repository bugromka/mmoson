#!/usr/bin/env python3
"""make_site_icons.py — рисует иконки-заменители для репозитория Image.

Зачем: страницы сайта ссылаются на файлы в
`Interregional-cartographic-yacluster/Image`, а репозитория пуста. Оригиналы
брендовых логотипов восстановить нельзя, поэтому здесь собираются
аккуратные нейтральные иконки для сервисов и организаций, у которых есть
общеизвестный знак (VK, MAX, Яндекс, почта, Добро.рф) и типовая эмблема для
Минстроя.

ВАЖНО: это заменители, а не официальные логотипы. Их задача — чтобы ссылки
на сайте не отдавали 404, пока не вернутся оригиналы. Файлы помечены в
README репозитория Image.

Запуск:
    python3 tools/make_site_icons.py                # в site/icons/
    python3 tools/make_site_icons.py --out DIR
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
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


def centered_text(draw: ImageDraw.ImageDraw, text: str, size: int, y: int, fill=(255, 255, 255, 255), bold=True):
    f = font(size, bold)
    box = draw.textbbox((0, 0), text, font=f)
    draw.text(((SIZE - (box[2] - box[0])) / 2 - box[0], y), text, font=f, fill=fill)


def envelope(draw: ImageDraw.ImageDraw, color=(255, 255, 255, 255)):
    x0, y0, x1, y1 = 48, 78, 208, 178
    draw.rounded_rectangle((x0, y0, x1, y1), radius=14, outline=color, width=10)
    draw.line((x0 + 8, y0 + 10, SIZE / 2, y0 + 52), fill=color, width=10)
    draw.line((x1 - 8, y0 + 10, SIZE / 2, y0 + 52), fill=color, width=10)


def heart(draw: ImageDraw.ImageDraw, cy: int = 104, scale: float = 1.0, color=(255, 255, 255, 255)):
    r = 34 * scale
    cx = SIZE / 2
    draw.ellipse((cx - 2 * r, cy - r, cx, cy + r), fill=color)
    draw.ellipse((cx, cy - r, cx + 2 * r, cy + r), fill=color)
    draw.polygon([(cx - 2 * r, cy + 2), (cx + 2 * r, cy + 2), (cx, cy + 3.1 * r)], fill=color)


def pin(draw: ImageDraw.ImageDraw, color=(255, 255, 255, 255)):
    cx, cy, r = SIZE / 2, 104, 52
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=12)
    draw.polygon([(cx - 26, cy + 34), (cx + 26, cy + 34), (cx, cy + 96)], fill=color)
    draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=color)


def building(draw: ImageDraw.ImageDraw, color=(255, 255, 255, 255)):
    draw.rectangle((72, 92, 184, 196), fill=color)
    draw.polygon([(64, 92), (192, 92), (128, 52)], fill=color)
    for col in (96, 124, 152):
        draw.rectangle((col, 112, col + 16, 132), fill=(31, 95, 169, 255))
        draw.rectangle((col, 148, col + 16, 168), fill=(31, 95, 169, 255))


def save(img: Image.Image, path: Path):
    img.save(path, "PNG", optimize=True)
    print(f"  {path.name}  {path.stat().st_size / 1024:.1f} КБ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "site" / "icons")
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    print(f"иконки в {out}")

    # VK
    img = rounded((0, 119, 255, 255))
    d = ImageDraw.Draw(img)
    centered_text(d, "VK", 118, 58)
    save(img, out / "Icon-Color.png")

    # MAX — мессенджер
    img = gradient((108, 92, 231), (0, 194, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((56, 72, 200, 168), radius=28, outline=(255, 255, 255, 255), width=10)
    d.polygon([(86, 168), (86, 206), (128, 168)], fill=(255, 255, 255, 255))
    save(img, out / "Max-logo-2025.png")

    # Почта
    img = rounded((143, 126, 214, 255))
    d = ImageDraw.Draw(img)
    envelope(d)
    save(img, out / "1200x630wa.png")

    # Добро.рф
    img = rounded((255, 107, 107, 255))
    d = ImageDraw.Draw(img)
    heart(d, cy=100, scale=0.80)
    centered_text(d, "ДОБРО", 34, 186)
    save(img, out / "6v-QBl8-L6mgk.png")

    # Яндекс
    img = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    centered_text(d, "Я", 168, 24, fill=(252, 63, 29, 255))
    save(img, out / "yandex-logo-rus.png")

    # Минстрой России — типовая эмблема
    img = rounded((31, 95, 169, 255))
    d = ImageDraw.Draw(img)
    building(d)
    centered_text(d, "МИНСТРОЙ", 26, 204)
    save(img, out / "Minstroy-RF.png")

    # КРЯК — знак-заменитель: контур карты и точка на ней
    img = rounded((143, 126, 214, 255), radius=128)
    d = ImageDraw.Draw(img)
    for i, w in enumerate((16, 12, 8)):
        d.arc((44 + i * 26, 44 + i * 26, 212 - i * 26, 212 - i * 26), start=200, end=340,
              fill=(255, 255, 255, 255), width=w)
    pin(d)
    save(img, out / "new-logo-kryak (1).png")

    print("\nготова памятка: README для репозитория Image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
