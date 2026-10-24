"""Create a deterministic, runtime-only local installation ZIP."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import re
import shutil
from audit_release import audit_bytes, audit_files, public_files, runtime_files

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = re.search(r'version\s*=\s*"([^"]+)"', (ROOT / "modinfo.lua").read_text(encoding="utf-8")).group(1)
    audit_files(public_files())
    paths = runtime_files() + [ROOT / name for name in ("README.md", "WORKSHOP_DESCRIPTION.bbcode", "art/preview.png")]
    (ROOT / "dist").mkdir(exist_ok=True)
    destination = ROOT / f"dist/Ta2BroFriedChicken-{version}.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            info = ZipInfo("Ta2BroFriedChicken/" + path.relative_to(ROOT).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    audit_bytes(destination.name, destination.read_bytes())
    workshop = ROOT / "dist/workshop/Ta2BroFriedChicken"
    expected = {p.relative_to(ROOT).as_posix() for p in runtime_files()}
    if workshop.exists():
        existing = {p.relative_to(workshop).as_posix() for p in workshop.rglob("*") if p.is_file()}
        if not existing.issubset(expected):
            raise ValueError("Unexpected files in Workshop staging area; use a clean staging area")
    for path in runtime_files():
        target = workshop / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    print(f"Built {destination.name}; clean Workshop content prepared.")


if __name__ == "__main__":
    main()
