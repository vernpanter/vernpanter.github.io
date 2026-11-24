"""Makes web sized copies of the art for the published site.

The copies go in derived/ and _data/images.json tells the templates where they
are. Both are rebuilt on every run and are never committed.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import NamedTuple, TypedDict

from PIL import Image, ImageOps

from artwork import SECTIONS, enable_heic, is_image, section_files, site_path

THUMB_SIZE = 800
LARGE_SIZE = 2000


class ImageEntry(TypedDict):
    thumb: str
    large: str
    width: int
    height: int


class Copy(NamedTuple):
    url: str
    width: int
    height: int


def save_copy(image: Image.Image, size: int, out: Path, stem: str) -> Copy:
    copy = image.copy()
    copy.thumbnail((size, size), Image.Resampling.LANCZOS)
    # A copy keeps the original's info, so clear it or WebP saves the EXIF
    # location and the color profile with it.
    profile = copy.info.get("icc_profile")
    copy.info.clear()
    name = f"{stem}-{size}.webp"
    if isinstance(profile, bytes):
        copy.save(out / name, "WEBP", quality=84, method=5, icc_profile=profile)
    else:
        copy.save(out / name, "WEBP", quality=84, method=5)
    return Copy(f"/derived/{name}", copy.width, copy.height)


def prepare(path: Path, out: Path) -> ImageEntry:
    stem = hashlib.sha256(path.read_bytes()).hexdigest()[:20]
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened)
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        profile = image.info.get("icc_profile")
        # A CMYK profile does not describe the RGB copy
        keep_profile = image.mode in ("RGB", "RGBA")
        image = image.convert("RGBA" if has_alpha else "RGB")
        image.info.clear()
        if keep_profile and isinstance(profile, bytes):
            image.info["icc_profile"] = profile
    thumb = save_copy(image, THUMB_SIZE, out, stem)
    large = save_copy(image, LARGE_SIZE, out, stem)
    return ImageEntry(
        thumb=thumb.url, large=large.url, width=thumb.width, height=thumb.height
    )


def prepare_all(root: Path) -> dict[str, ImageEntry]:
    enable_heic()
    out = root / "derived"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    entries: dict[str, ImageEntry] = {}
    for section in SECTIONS:
        for path in section_files(root, section):
            if is_image(path):
                entries[site_path(root, path)] = prepare(path, out)
    data = root / "_data" / "images.json"
    data.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    return entries


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"Prepared {len(prepare_all(root))} images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
