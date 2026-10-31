#!/usr/bin/env python3
"""upload_images.py — загрузка изображений сайта в репозиторий Image.

Кладёт файлы из локальной папки в
`Interregional-cartographic-yacluster/Image` под теми же именами, которые
ждут страницы сайта (см. site/IMAGE-MANIFEST.md). Каждый файл пишется
отдельным коммитом в ветку main через GitHub API, поэтому права и токен
берутся из окружения `gh` — ничего дополнительно настраивать не нужно.

Использование:
    python3 tools/upload_images.py <папка>
    python3 tools/upload_images.py <папка> --dry-run
    python3 tools/upload_images.py <папка> --only pervie.png "Max-logo-2025.png"

Требования:
    * установлен и авторизован `gh` (проверка: `gh auth status`);
    * у токена есть право push в указанный репозиторий.

Скрипт не удаляет и не перезаписывает чужие файлы: существующий файл
пропускается, если не указан --force.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

REPO = "Interregional-cartographic-yacluster/Image"
BRANCH = "main"

# Имена, которые ждут страницы сайта (site/IMAGE-MANIFEST.md).
EXPECTED = [
    "0a9eddda-1151-4a5d-be30-bd569f4561d7.png",
    "1200x630wa.png",
    "5210887725371226426.png",
    "521088772537122642625.png",
    "521088772537122642626.png",
    "52108877253712264263.png",
    "6v-QBl8-L6mgk.png",
    "798853bbaecb9b291bef12d7196f5f7f.png",
    "9-Yfgu-BL3tt-E.png",
    "H6mbi7ew-VW8.png",
    "Icon-Color.png",
    "Max-logo-2025.png",
    "Minstroy-RF.png",
    "Phi-NXMWd7-Nto-Iw-Hj-S65t-N84-Nc-Fz-ILdgt-P-T4-KEab-UOqy8gg3-MTwr-WIWOl-HO1-MJb-Vv-YH3j-Eo-WFLWMx7-5.png",
    "Phi-NXMWd7-Nto-Iw-Hj-S65t-N84-Nc-Fz-ILdgt-P-T4-KEab-UOqy8gg3-MTwr-WIWOl-HO1-MJb-Vv-YH3j-Eo-WFLWMx7-5o-EHI.png",
    "Slide-16-9-43-2.png",
    "TSU.png",
    "Vmake-1732993238.png",
    "d-COb-Vlpi-M-xa-Z4-BZdk-KEr-Ujb15-Gs2zt-Ey156-Mk-ARP5-ix-Tv3gc-ORi-KGl1-UG0n-v-H4-V005-Md-Hct-Ga-Ubw1-YC0h.jpg",
    "ez-DLp34-Rz-g.png",
    "image (2).png",
    "img1_361.png",
    "is7y3-uk-D8o.png",
    "kursk-511x533.png",
    "lingvistznanie.png",
    "new-logo-kryak (1).png",
    "nex-Ufo-Sv-X0-m0-C2ov-Gh-lh-Al-Fl-Pl6qoe-KLFSQ7-MHi9-Z3-VUfu-En-Okzk-Nv-RLfvt-PRo2r2t-Rw1dj-Kn3-RNna-FVQl.png",
    "pervie.png",
    "school59_kursk.png",
    "yandex-logo-rus.png",
]

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}


def gh_api(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    cmd = ["gh", "api", "-X", method, path]
    if payload is not None:
        cmd += ["--input", "-"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        data = {"raw": proc.stdout}
    return proc.returncode, data


def file_exists(name: str) -> bool:
    quoted = name.replace(" ", "%20").replace("#", "%23")
    code, _ = gh_api("GET", f"repos/{REPO}/contents/{quoted}?ref={BRANCH}")
    return code == 0


def upload(path: Path, force: bool) -> str:
    name = path.name
    if name not in EXPECTED:
        return f"ПРОПУЩЕН (имя не из списка сайта): {name}"
    if not force and file_exists(name):
        return f"ПРОПУЩЕН (уже есть в репозитории): {name}"

    payload = {
        "message": f"Restore site image: {name}",
        "content": base64.b64encode(path.read_bytes()).decode("ascii"),
        "branch": BRANCH,
    }
    quoted = name.replace(" ", "%20").replace("#", "%23")
    if force:
        code, data = gh_api("GET", f"repos/{REPO}/contents/{quoted}?ref={BRANCH}")
        if code == 0 and isinstance(data, dict) and data.get("sha"):
            payload["sha"] = data["sha"]

    code, data = gh_api("PUT", f"repos/{REPO}/contents/{quoted}", payload)
    if code != 0:
        return f"ОШИБКА {name}: {data.get('message', data)}"
    return f"загружен: {name} ({path.stat().st_size/1024:.0f} КБ)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Загрузка изображений сайта в репозиторий Image")
    ap.add_argument("folder", type=Path, help="папка с изображениями")
    ap.add_argument("--dry-run", action="store_true", help="только показать, что будет сделано")
    ap.add_argument("--force", action="store_true", help="перезаписать существующие файлы")
    ap.add_argument("--only", nargs="+", metavar="ФАЙЛ", help="загрузить только указанные файлы")
    args = ap.parse_args()

    if not args.folder.is_dir():
        print(f"нет такой папки: {args.folder}", file=sys.stderr)
        return 1

    files = sorted(p for p in args.folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXT)
    if args.only:
        wanted = set(args.only)
        files = [p for p in files if p.name in wanted]

    if not files:
        print("в папке нет подходящих файлов", file=sys.stderr)
        return 1

    present = {p.name for p in files}
    missing = [n for n in EXPECTED if n not in present]
    print(f"репозиторий: {REPO}, ветка {BRANCH}")
    print(f"к загрузке: {len(files)} файлов\n")

    if args.dry_run:
        for p in files:
            mark = " ok " if p.name in EXPECTED else " не из списка "
            print(f"[{mark}] {p.name} ({p.stat().st_size/1024:.0f} КБ)")
    else:
        for p in files:
            print(upload(p, args.force))

    if missing:
        print(f"\nещё не хватает {len(missing)} файлов из списка сайта:")
        for n in missing:
            print(f"  - {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
