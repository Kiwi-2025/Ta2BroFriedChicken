"""Audit an explicit public-file allowlist before GitHub or Workshop release."""
from pathlib import Path
import argparse
import io
import re
import struct
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ("modinfo.lua", "modmain.lua", "modicon.xml", "modicon.tex", "preview.jpg")
TOOLS = ("build_assets.py", "test_mod.py", "package_mod.py", "audit_release.py", "requirements.txt")
TEXT_SUFFIXES = {".lua", ".xml", ".md", ".txt", ".py", ".bbcode", ".json"}
PRIVATE_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/][A-Za-z0-9_]"),
    re.compile(rb"/(?:Users|home|mnt|media)/[A-Za-z0-9_]"),
    re.compile(rb"KU_[A-Za-z0-9]{6,}"),
    re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
PNG_METADATA = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"caBX"}


def runtime_files():
    paths = [ROOT / name for name in RUNTIME_ROOT]
    paths += sorted((ROOT / "scripts").rglob("*.lua"))
    paths += sorted(p for p in (ROOT / "images").rglob("*") if p.suffix in {".tex", ".xml"})
    paths += [ROOT / "anim/ta2bro_chicken.zip"]
    return paths


def public_files():
    paths = runtime_files()
    paths += [ROOT / name for name in (".gitignore", "README.md", "WORKSHOP_DESCRIPTION.bbcode", "art/README.md", "art/preview.png")]
    paths += [ROOT / "tools" / name for name in TOOLS]
    paths += [ROOT / f"art/source/ta2bro_chicken_{flavor}.png" for flavor in ("spicy", "garlic", "soy")]
    return sorted(set(paths))


def audit_bytes(name, data):
    suffix = Path(name).suffix.lower()
    if suffix in TEXT_SUFFIXES or name == ".gitignore":
        data.decode("utf-8")
        if any(pattern.search(data) for pattern in PRIVATE_PATTERNS):
            raise ValueError(f"Possible personal data in {name}")
    elif suffix == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid PNG: {name}")
        offset = 8
        while offset < len(data):
            length = struct.unpack_from(">I", data, offset)[0]
            kind = data[offset + 4:offset + 8]
            if kind in PNG_METADATA:
                raise ValueError(f"Remove non-image metadata from {name}")
            offset += 12 + length
    elif suffix in {".jpg", ".jpeg"}:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "JPEG" or image.getexif() or image.info.get("xmp") or image.info.get("comment"):
                raise ValueError(f"JPEG must be an image without personal metadata: {name}")
    elif suffix == ".zip":
        with ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError(f"Corrupt archive: {name}")
            for member in archive.infolist():
                if member.is_dir():
                    continue
                if member.filename.startswith(("/", "\\")) or ".." in Path(member.filename).parts:
                    raise ValueError(f"Unsafe archive member in {name}")
                audit_bytes(member.filename, archive.read(member))


def audit_files(paths):
    for path in paths:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Public files must belong to this project")
        audit_bytes(path.relative_to(ROOT).as_posix(), path.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", action="store_true", help="Write a relative public-file manifest")
    parser.add_argument("--archive", type=Path, help="Also audit a release archive")
    args = parser.parse_args()
    paths = public_files()
    audit_files(paths)
    if args.archive:
        audit_bytes(args.archive.name, args.archive.read_bytes())
    if args.manifest:
        (ROOT / "dist").mkdir(exist_ok=True)
        (ROOT / "dist/public-files.txt").write_text("\n".join(path.relative_to(ROOT).as_posix() for path in paths) + "\n", encoding="utf-8")
    print(f"Privacy audit passed: {len(paths)} public files; no personal paths, identifiers, credentials or PNG metadata found.")


if __name__ == "__main__":
    main()
