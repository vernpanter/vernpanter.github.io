"""Finds the uploaded images, shared by the other scripts."""

from collections.abc import Callable
from pathlib import Path
from typing import cast

import pillow_heif

SECTIONS = ("2d", "3d")
BROWSER_TYPES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"})
IMAGE_TYPES = BROWSER_TYPES | {".heic", ".heif"}


def enable_heic() -> None:
    """Let Pillow open the HEIC photos iPhones take."""
    # pillow_heif leaves **kwargs untyped
    register = cast(
        Callable[[], None],
        pillow_heif.register_heif_opener,  # pyright: ignore[reportUnknownMemberType]
    )
    register()


def section_files(root: Path, section: str) -> list[Path]:
    """Return every file uploaded to a section, without READMEs and dotfiles."""
    folder = root / "art" / section
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.name.lower() != "readme.md"
        and not any(part.startswith(".") for part in path.relative_to(folder).parts)
    )


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_TYPES


def is_placeholder(key: str) -> bool:
    """Return whether a work only stands in until there is real art."""
    return key.lower().startswith("placeholder")


def work_key(root: Path, section: str, path: Path) -> str:
    """Return the name that identifies a work, its file or its folder."""
    return path.relative_to(root / "art" / section).parts[0]


def site_path(root: Path, path: Path) -> str:
    """Return the path the way Jekyll writes it, with a leading slash."""
    return "/" + path.relative_to(root).as_posix()
