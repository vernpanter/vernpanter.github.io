"""Builds the real templates with made up art, with and without the copies."""

import html
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from artwork import enable_heic
from check_site import check_built
from prepare_images import prepare_all

enable_heic()

SITE_PARTS = ("_config.yml", "_layouts", "_includes", "_data", "assets", "art",
              "2d.html", "3d.html", "404.html", "about.md", "contact.md", "cv.md",
              "index.html", "README.md", "DEVELOPMENT.md", "Gemfile", "Gemfile.lock")
ACCENTED = unicodedata.normalize("NFD", "Café señor.jpg")

# One odd name per way a file name can break a URL or the page
FLAT = ("zebra.jpg", "apple-tree.JPG", "Old House #4.png", "50% off?.jpg",
        ACCENTED, 'Tom & "Jo" <3.jpg', "v1.2 study.webp")


def build(root: Path) -> Path:
    result = subprocess.run(
        ["bundle", "exec", "jekyll", "build", "--strict_front_matter"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return root / "_site"


def titles(page: str) -> list[str]:
    return [html.unescape(t) for t in re.findall(r"<cite>(.+?)</cite>", page)]


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve()
        for name in SITE_PARTS:
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, self.root / name)
            else:
                shutil.copy2(source, self.root / name)
        # Start from a known place whatever the artist has uploaded
        (self.root / "_data/images.json").unlink(missing_ok=True)
        shutil.rmtree(self.root / "art")
        for section in ("2d", "3d"):
            (self.root / "art" / section).mkdir(parents=True)
            (self.root / "art" / section / "README.md").write_text("# Notes\n")
            self.data(f"works_{section}.yml", "# nothing yet\n")
        self.data("artist.yml", 'name: "Test Artist"\nemail: ""\nhome_image: ""\nlinks: []\n')

    def data(self, name: str, text: str) -> None:
        (self.root / "_data" / name).write_text(text, encoding="utf-8")

    def picture(self, name: str) -> None:
        path = self.root / "art" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (90, 60)).save(path)

    def fill(self) -> None:
        for name in FLAT:
            self.picture(f"2d/{name}")
        for view in ("1 front.jpg", "2 back.jpg", "3 side.jpg"):
            self.picture(f"3d/tall-bird/{view}")
        self.picture("3d/small_bowl.jpg")
        self.data("works_2d.yml", '- file: "zebra.jpg"\n  title: "Stripes"\n  year: 2026\n'
                                  '  medium: "Oil"\n- file: "v1.2 study.webp"\n')
        self.data("works_3d.yml", '- file: "small_bowl.jpg"\n  size: "3 x 3 in"\n')

    def page(self, site: Path, name: str) -> str:
        return (site / name / "index.html").read_text(encoding="utf-8")

    def check(self, site: Path) -> None:
        problems: list[str] = []
        check_built(site, problems)
        self.assertEqual(problems, [])

    def check_galleries(self, site: Path) -> None:
        flat, solid = self.page(site, "2d"), self.page(site, "3d")
        self.assertEqual(titles(flat)[:2], ["Stripes", "V1.2 study"])
        self.assertEqual(
            sorted(unicodedata.normalize("NFC", t) for t in titles(flat)[2:]),
            sorted(["Apple tree", "Old House #4", "50% off?", "Café señor", 'Tom & "Jo" <3']),
        )
        self.assertEqual(titles(solid), ["Small bowl", "Tall bird"])
        self.assertEqual(solid.count('data-total="3"'), 3)
        self.assertNotIn("Tall bird", flat)
        self.assertNotIn("Stripes", solid)
        # size is blank for Stripes, and Liquid would print the field count
        self.assertIn('data-label="Oil"', flat)
        self.assertIn('data-label="3 x 3 in"', solid)
        self.check(site)

    def test_empty_site(self) -> None:
        site = build(self.root)
        for section in ("2d", "3d"):
            self.assertIn("New work is coming soon", self.page(site, section))
        self.assertIn("coming soon", self.page(site, "contact"))
        self.assertFalse((site / "art").exists())
        self.check(site)

    def test_guides_are_not_published(self) -> None:
        site = build(self.root)
        files = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
        names = [f for f in files if "readme" in f.lower() or "development" in f.lower()]
        self.assertEqual(names, [])
        self.assertNotIn("How to manage", (site / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(f for f in files if f.endswith(".html")),
            ["2d/index.html", "3d/index.html", "404.html", "about/index.html",
             "contact/index.html", "cv/index.html", "index.html"],
        )

    def test_uploads_only(self) -> None:
        self.fill()
        self.picture("3d/tall-bird/4 phone.heic")
        site = build(self.root)
        self.check_galleries(site)
        self.assertIn("/art/2d/zebra.jpg", (site / "index.html").read_text())
        sources = re.findall(r'src="(/art/[^"]+)"', self.page(site, "2d"))
        self.assertEqual(len(sources), len(FLAT))
        for source in sources:
            self.assertTrue((site / unquote(html.unescape(source)).lstrip("/")).is_file(), source)

    def test_with_copies(self) -> None:
        self.fill()
        self.picture("3d/bowl phone.heic")
        prepare_all(self.root)
        site = build(self.root)
        shutil.rmtree(site / "art")
        self.assertIn("Bowl phone", titles(self.page(site, "3d")))
        self.assertNotIn("/art/", self.page(site, "2d"))
        self.assertNotIn("/art/", (site / "index.html").read_text())
        (self.root / "art/3d/bowl phone.heic").unlink()
        prepare_all(self.root)
        site = build(self.root)
        shutil.rmtree(site / "art")
        self.check_galleries(site)

    def test_artist_settings(self) -> None:
        self.fill()
        self.data("artist.yml", 'name: "A & B"\nemail: "a@example.com"\n'
                                'home_image: "art/3d/tall-bird/2 back.jpg"\n'
                                'links:\n  - name: "Shop"\n    link: "https://example.com/?a=1&b=2"\n')
        site = build(self.root)
        home = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn("2%20back.jpg", home)
        self.assertIn('class="home-image" href="/3d/"', home)
        self.assertIn("A &amp; B", home)
        contact = self.page(site, "contact")
        self.assertIn("mailto:a@example.com", contact)
        self.assertIn("https://example.com/?a=1&amp;b=2", contact)


if __name__ == "__main__":
    unittest.main()
