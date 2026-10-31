#!/usr/bin/env python3
"""nik_vault.py — сейф для приватной папки NIK/.

Шифрует каталог в один файл-контейнер. Ключ выводится из пароля, который
вводит человек; пароль нигде не сохраняется (ни в контейнере, ни в репозитории,
ни в этом скрипте).

Криптосхема (только stdlib + openssl, никаких зависимостей):
    scrypt(N=2^15, r=8, p=1, dklen=64) -> enc_key(32) + mac_key(32)
    AES-256-CBC (openssl enc), случайные salt(16) и iv(16)
    HMAC-SHA256 по заголовку и шифртексту (encrypt-then-MAC)

Формат контейнера .nikvault:
    "NIKVAULT1"            9 байт
    salt                  16 байт
    iv                    16 байт
    ciphertext             N байт (AES-256-CBC/PKCS7 от tar.gz)
    mac                   32 байта (HMAC-SHA256, обрезать нельзя)

Использование:
    python3 tools/nik_vault.py lock   NIK [--out DIR] [--remove-source]
    python3 tools/nik_vault.py verify FILE.nikvault
    python3 tools/nik_vault.py unlock FILE.nikvault [--dest DIR] [--force]
    python3 tools/nik_vault.py list   FILE.nikvault

Пароль: интерактивный ввод (getpass) либо файл с паролем, путь к которому
задан --passphrase-file или переменной NIK_VAULT_PASSPHRASE_FILE.
Пароль НЕЛЬЗЯ передавать аргументом командной строки — он попадёт в ps.

Потеря пароля = потеря содержимого. Резервная копия контейнера обязательна.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAGIC = b"NIKVAULT1"
SALT_LEN = 16
IV_LEN = 16
MAC_LEN = 32
KEY_LEN = 32
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 128 * 1024 * 1024
CHUNK = 1 << 20


class VaultError(RuntimeError):
    pass


# ---------------------------------------------------------------- пароль


def _read_passphrase_file(path: Path) -> bytes:
    if not path.is_file():
        raise VaultError(f"файл пароля не найден: {path}")
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        print(
            f"ВНИМАНИЕ: {path} доступен группе/остальным (права {oct(mode)}). "
            f"Выполни: chmod 600 {path}",
            file=sys.stderr,
        )
    return path.read_bytes().rstrip(b"\r\n")


def get_passphrase(confirm: bool, file_hint: str | None) -> bytes:
    if file_hint:
        return _read_passphrase_file(Path(file_hint).expanduser())
    env_file = os.environ.get("NIK_VAULT_PASSPHRASE_FILE")
    if env_file:
        return _read_passphrase_file(Path(env_file).expanduser())
    if not sys.stdin.isatty():
        raise VaultError(
            "нет терминала для ввода пароля. Задай --passphrase-file PATH "
            "или переменную NIK_VAULT_PASSPHRASE_FILE."
        )
    first = getpass.getpass("Пароль сейфа: ").encode()
    if len(first) < 12:
        raise VaultError("пароль короче 12 символов — так нельзя")
    if confirm:
        again = getpass.getpass("Повтори пароль: ").encode()
        if first != again:
            raise VaultError("пароли не совпадают")
    return first


def derive_keys(passphrase: bytes, salt: bytes) -> tuple[bytes, bytes]:
    dk = hashlib.scrypt(
        passphrase,
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_LEN * 2,
        maxmem=SCRYPT_MAXMEM,
    )
    return dk[:KEY_LEN], dk[KEY_LEN:]


# ---------------------------------------------------------------- openssl


def _openssl(data_in: Path, data_out: Path, key: bytes, iv: bytes, decrypt: bool) -> None:
    cmd = [
        "openssl", "enc",
        "-aes-256-cbc", "-nosalt",
        "-K", key.hex(),
        "-iv", iv.hex(),
    ]
    if decrypt:
        cmd.insert(2, "-d")
    with data_in.open("rb") as fin, data_out.open("wb") as fout:
        proc = subprocess.run(cmd, stdin=fin, stdout=fout, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise VaultError(f"openssl завершился с ошибкой: {proc.stderr.decode(errors='replace').strip()}")


# ---------------------------------------------------------------- утилиты


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _mac(mac_key: bytes, salt: bytes, iv: bytes, ct_path: Path) -> bytes:
    h = hmac.new(mac_key, digestmod=hashlib.sha256)
    h.update(MAGIC)
    h.update(salt)
    h.update(iv)
    with ct_path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.digest()


def _read_header(f) -> tuple[bytes, bytes]:
    magic = f.read(len(MAGIC))
    if magic != MAGIC:
        raise VaultError("это не контейнер .nikvault")
    salt = f.read(SALT_LEN)
    iv = f.read(IV_LEN)
    if len(salt) != SALT_LEN or len(iv) != IV_LEN:
        raise VaultError("контейнер обрезан")
    return salt, iv


# ---------------------------------------------------------------- команды


def cmd_lock(args) -> int:
    src = Path(args.path).expanduser().resolve()
    if not src.is_dir():
        raise VaultError(f"нет каталога: {src}")
    out_dir = Path(args.out).expanduser().resolve() if args.out else Path.home() / "nik-vault"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    vault = out_dir / f"{src.name}-{stamp}.nikvault"
    if vault.exists():
        raise VaultError(f"файл уже существует: {vault}")

    files = [p for p in src.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print(f"Источник : {src}")
    print(f"Файлов   : {len(files)}  ({total / 1024:.1f} КиБ)")
    print(f"Контейнер: {vault}")

    passphrase = get_passphrase(confirm=True, file_hint=args.passphrase_file)
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    enc_key, mac_key = derive_keys(passphrase, salt)

    tmpdir = Path(tempfile.mkdtemp(prefix="nikvault-"))
    tar_path = tmpdir / "payload.tar.gz"
    ct_path = tmpdir / "payload.bin"
    try:
        os.chmod(tmpdir, 0o700)
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(src, arcname=src.name)
        _openssl(tar_path, ct_path, enc_key, iv, decrypt=False)

        mac = _mac(mac_key, salt, iv, ct_path)
        tmp_vault = vault.with_suffix(".part")
        with tmp_vault.open("wb") as f:
            f.write(MAGIC)
            f.write(salt)
            f.write(iv)
            with ct_path.open("rb") as ct:
                shutil.copyfileobj(ct, f, CHUNK)
            f.write(mac)
        os.chmod(tmp_vault, 0o600)
        os.replace(tmp_vault, vault)

        if not args.no_verify:
            print("Проверка: расшифровываю контейнер обратно и сверяю хэш...")
            check_dir = Path(tempfile.mkdtemp(prefix="nikvault-check-"))
            try:
                check_tar = check_dir / "check.tar.gz"
                _extract_payload(vault, passphrase, check_tar)
                if _sha256(check_tar) != _sha256(tar_path):
                    raise VaultError("проверка не прошла: содержимое контейнера не совпало")
            finally:
                shutil.rmtree(check_dir, ignore_errors=True)
            print("Проверка: OK")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\nГотово: {vault}  ({vault.stat().st_size / 1024:.1f} КиБ)")

    if args.remove_source:
        confirm = input(
            f"\nУДАЛИТЬ открытый каталог {src}? Это необратимо.\n"
            f"Введи ровно 'удалить' для подтверждения: "
        ).strip()
        if confirm == "удалить":
            shutil.rmtree(src)
            print(f"Удалено: {src}. Контейнер остался единственной копией.")
        else:
            print("Открытый каталог оставлен на месте.")
    else:
        print("Открытый каталог НЕ тронут. Удалить его можно так: "
              f"python3 {sys.argv[0]} lock {src} --remove-source")
    return 0


def _extract_payload(vault: Path, passphrase: bytes, dest_tar: Path) -> None:
    with vault.open("rb") as f:
        salt, iv = _read_header(f)
        enc_key, mac_key = derive_keys(passphrase, salt)
        tmpdir = Path(tempfile.mkdtemp(prefix="nikvault-open-"))
        try:
            os.chmod(tmpdir, 0o700)
            body = tmpdir / "body.bin"
            with body.open("wb") as out:
                shutil.copyfileobj(f, out, CHUNK)
            if body.stat().st_size <= MAC_LEN:
                raise VaultError("контейнер обрезан")
            ct_path = tmpdir / "ct.bin"
            with body.open("rb") as b, ct_path.open("wb") as c:
                remaining = body.stat().st_size - MAC_LEN
                while remaining > 0:
                    block = b.read(min(CHUNK, remaining))
                    if not block:
                        break
                    c.write(block)
                    remaining -= len(block)
                stored_mac = b.read(MAC_LEN)
            expected = _mac(mac_key, salt, iv, ct_path)
            if not hmac.compare_digest(stored_mac, expected):
                raise VaultError("неверный пароль или контейнер повреждён")
            _openssl(ct_path, dest_tar, enc_key, iv, decrypt=True)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


def cmd_verify(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    passphrase = get_passphrase(confirm=False, file_hint=args.passphrase_file)
    tmpdir = Path(tempfile.mkdtemp(prefix="nikvault-verify-"))
    try:
        tar_path = tmpdir / "payload.tar.gz"
        _extract_payload(vault, passphrase, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            members = tar.getmembers()
            size = sum(m.size for m in members if m.isfile())
        print(f"OK: MAC верен, архив читается. Элементов: {len(members)}, суммарно {size / 1024:.1f} КиБ")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


def cmd_list(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    passphrase = get_passphrase(confirm=False, file_hint=args.passphrase_file)
    tmpdir = Path(tempfile.mkdtemp(prefix="nikvault-list-"))
    try:
        tar_path = tmpdir / "payload.tar.gz"
        _extract_payload(vault, passphrase, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            for m in tar.getmembers():
                kind = "d" if m.isdir() else "-"
                print(f"{kind} {m.size:>9}  {m.name}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


def cmd_unlock(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve() if args.dest else Path.cwd() / "NIK"
    if dest.exists() and not args.force:
        raise VaultError(f"{dest} уже существует; укажи --dest или --force")
    passphrase = get_passphrase(confirm=False, file_hint=args.passphrase_file)
    tmpdir = Path(tempfile.mkdtemp(prefix="nikvault-unlock-"))
    try:
        tar_path = tmpdir / "payload.tar.gz"
        _extract_payload(vault, passphrase, tar_path)
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, "r:gz") as tar:
            try:
                tar.extractall(dest, filter="data")  # Python >= 3.12
            except TypeError:
                tar.extractall(dest)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"Распаковано в {dest}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Шифрованный сейф для приватной папки NIK/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--passphrase-file", help="файл с паролем (по умолчанию — интерактивный ввод)")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("lock", help="зашифровать каталог в контейнер")
    p.add_argument("path")
    p.add_argument("--out", help="каталог для контейнера (по умолчанию ~/nik-vault)")
    p.add_argument("--remove-source", action="store_true", help="предложить удалить открытый каталог")
    p.add_argument("--no-verify", action="store_true", help="не проверять контейнер обратной расшифровкой")
    p.set_defaults(func=cmd_lock)

    p = sub.add_parser("verify", help="проверить MAC и читаемость контейнера")
    p.add_argument("vault")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("list", help="показать содержимое контейнера")
    p.add_argument("vault")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("unlock", help="расшифровать контейнер в каталог")
    p.add_argument("vault")
    p.add_argument("--dest", help="куда распаковать (по умолчанию ./NIK)")
    p.add_argument("--force", action="store_true", help="разрешить распаковку в существующий каталог")
    p.set_defaults(func=cmd_unlock)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except VaultError as exc:
        print(f"ОШИБКА: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nПрервано.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
