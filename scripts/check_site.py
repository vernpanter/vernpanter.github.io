"""Checks the files the artist edits, and the built pages with --built.

Problems are printed in plain language, since the person reading them may have
only ever used the GitHub website.
"""

import argparse
import posixpath
import re
import sys
from collections.abc import Mapping, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlsplit

import yaml
from PIL import Image, UnidentifiedImageError

from artwork import SECTIONS, enable_heic, is_image, section_files, work_key

WORK_FIELDS = frozenset({"file", "title", "year", "medium", "size", "description"})
ARTIST_FIELDS = frozenset({"name", "tagline", "email", "home_image", "links"})
# Jekyll leaves out names that start with these
SKIPPED_STARTS = ("_", "#", "~")


def load_yaml(path: Path, problems: list[str]) -> object:
    where = f"_data/{path.name}"
    if not path.exists():
        problems.append(f"{where} is missing.")
        return None
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*(?:-\s+)?\w+:\s+[^\"'#\s][^\"]*\s#", line):
            problems.append(
                f"{where} line {number}: put quote marks around the text, "
                "everything after # is ignored without them."
            )
    try:
        # safe_load is typed as Any in the stubs
        return cast(object, yaml.safe_load(text))
    except yaml.MarkedYAMLError as error:
        mark = error.problem_mark
        line = f" near line {mark.line + 1}" if mark else ""
        problems.append(
            f"{where}{line} cannot be read. Check the quote marks and that each "
            f"line lines up with the one above it. ({error.problem})"
        )
    except yaml.YAMLError as error:
        problems.append(f"{where} cannot be read. ({error})")
    return None


def text_of(value: object) -> str | None:
    """Return a data value as text, or None when it is not text or a number."""
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def check_works(root: Path, section: str, problems: list[str]) -> None:
    where = f"_data/works_{section}.yml"
    data = load_yaml(root / where, problems)
    if data is None:
        return
    if not isinstance(data, list):
        problems.append(f"{where}: each work has to start with - file:")
        return
    keys = {
        work_key(root, section, path).lower()
        for path in section_files(root, section)
        if is_image(path)
    }
    seen: set[str] = set()
    # isinstance only narrows to list[Unknown]
    for number, item in enumerate(cast(list[object], data), 1):
        if not isinstance(item, dict):
            problems.append(f"{where}: entry {number} has to start with - file:")
            continue
        # isinstance only narrows to dict[Unknown, Unknown]
        entry = cast(Mapping[object, object], item)
        file = text_of(entry.get("file"))
        if not file:
            problems.append(f"{where}: entry {number} has no file.")
            continue
        for field, value in entry.items():
            if field not in WORK_FIELDS:
                problems.append(f'{where}: "{file}" has an unknown field "{field}".')
            elif text_of(value) is None:
                problems.append(
                    f'{where}: "{file}" needs quote marks around its {field}, '
                    "or delete that line."
                )
        if file.lower() in seen:
            problems.append(f'{where}: "{file}" is listed twice.')
        seen.add(file.lower())
        if file.lower() not in keys:
            problems.append(
                f'{where}: there is no "{file}" in art/{section}. Check the spelling, '
                "a file name needs its ending, like .jpg."
            )


def check_artist(root: Path, problems: list[str]) -> None:
    where = "_data/artist.yml"
    data = load_yaml(root / where, problems)
    if data is None:
        return
    if not isinstance(data, dict):
        problems.append(f"{where}: each line has to look like name: \"text\".")
        return
    # isinstance only narrows to dict[Unknown, Unknown]
    artist = cast(Mapping[object, object], data)
    if not text_of(artist.get("name")):
        problems.append(f"{where}: the name is empty.")
    for field, value in artist.items():
        if field not in ARTIST_FIELDS:
            problems.append(f'{where}: unknown field "{field}".')
        elif field != "links" and value is not None and text_of(value) is None:
            problems.append(f"{where}: put quote marks around the {field}.")
    home = text_of(artist.get("home_image"))
    if home:
        path = root / home.lstrip("/")
        arts = {p for section in SECTIONS for p in section_files(root, section)}
        if path not in arts:
            problems.append(f'{where}: there is no picture at "{home}".')
    links = artist.get("links")
    if links is None:
        return
    if not isinstance(links, list):
        problems.append(f"{where}: links has to be a list, or [] for none.")
        return
    # isinstance only narrows to list[Unknown]
    for link in cast(list[object], links):
        item: Mapping[object, object] = {}
        if isinstance(link, dict):
            # isinstance only narrows to dict[Unknown, Unknown]
            item = cast(Mapping[object, object], link)
        target = text_of(item.get("link"))
        if not text_of(item.get("name")) or not target:
            problems.append(f"{where}: every link needs a name and a link.")
        elif not target.startswith(("https://", "http://")):
            problems.append(f'{where}: the link "{target}" has to start with https://')


def check_images(root: Path, problems: list[str]) -> None:
    enable_heic()
    for section in SECTIONS:
        for path in section_files(root, section):
            name = path.relative_to(root).as_posix()
            parts = path.relative_to(root / "art" / section).parts
            if any(part.startswith(SKIPPED_STARTS) for part in parts):
                problems.append(f"{name}: names cannot start with _, # or ~")
            if not is_image(path):
                problems.append(f"{name}: this is not a picture the site can show.")
                continue
            try:
                with Image.open(path) as image:
                    image.load()
            except (UnidentifiedImageError, OSError) as error:
                problems.append(f"{name}: the picture is damaged, upload it again. ({error})")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []
        self.missing_alt = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: Sequence[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        for name in ("href", "src"):
            target = values.get(name)
            if target:
                self.targets.append(target)
        # The viewer's empty image gets its alt text from the script
        if tag == "img" and "src" in values and not values.get("alt"):
            self.missing_alt += 1
        if tag == "h1":
            self.h1_count += 1


def check_built(site: Path, problems: list[str]) -> None:
    pages = sorted(site.rglob("*.html"))
    # A Mac ignores case and how accents are stored, the web server does not
    files = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    if not pages:
        problems.append(f"{site} has no pages.")
    for page in pages:
        name = page.relative_to(site).as_posix()
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        if parser.missing_alt:
            problems.append(f"{name}: {parser.missing_alt} images have no alt text.")
        if parser.h1_count != 1:
            problems.append(f"{name}: has {parser.h1_count} h1 headings, expected 1.")
        for target in parser.targets:
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            link = posixpath.join("/", name, "..", unquote(parts.path))
            path = posixpath.normpath(link).lstrip("/")
            if files.isdisjoint((path, posixpath.join(path, "index.html"))):
                problems.append(f"{name}: broken link to {target}")


def find_problems(root: Path, built: Path | None) -> list[str]:
    problems: list[str] = []
    check_artist(root, problems)
    for section in SECTIONS:
        check_works(root, section, problems)
    check_images(root, problems)
    if built:
        check_built(built, problems)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--built", type=Path)
    args = parser.parse_args(namespace=Options())
    problems = find_problems(args.root.resolve(), args.built)
    for problem in problems:
        print(f"PROBLEM: {problem}", file=sys.stderr)
    return 1 if problems else 0


class Options(argparse.Namespace):
    root: Path
    built: Path | None


if __name__ == "__main__":
    sys.exit(main())
