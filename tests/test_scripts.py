"""Tests for the scripts. These do not need Ruby."""

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from artwork import enable_heic
from check_site import check_built, find_problems
from prepare_images import prepare_all

enable_heic()

GPS_IFD = 0x8825
ORIENTATION = 0x0112


class SiteCase(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve()
        for name in ("art/2d", "art/3d", "_data"):
            (self.root / name).mkdir(parents=True)
        self.write("artist.yml", 'name: "Test Artist"\nlinks: []\n')
        self.write("works_2d.yml", "# nothing yet\n")
        self.write("works_3d.yml", "# nothing yet\n")

    def write(self, name: str, text: str) -> None:
        (self.root / "_data" / name).write_text(text, encoding="utf-8")

    def picture(self, name: str, mode: str = "RGB", size: tuple[int, int] = (60, 40)) -> Path:
        path = self.root / "art" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new(mode, size).save(path)
        return path

    def assert_problem(self, text: str) -> None:
        problems = find_problems(self.root, None)
        self.assertTrue(any(text in p for p in problems), problems)


class CheckTests(SiteCase):
    def test_empty_site_is_fine(self) -> None:
        self.assertEqual(find_problems(self.root, None), [])

    def test_good_details_are_fine(self) -> None:
        self.picture("2d/Blue Door.JPG")
        self.picture("3d/tall-bird/front.jpg")
        self.write("works_2d.yml", '- file: "blue door.jpg"\n  title: "Untitled #4"\n  year: 2026\n')
        self.write("works_3d.yml", '- file: "tall-bird"\n  size: "12 x 6 in"\n')
        self.assertEqual(find_problems(self.root, None), [])

    def test_broken_yaml(self) -> None:
        self.write("works_2d.yml", '- file: "a.jpg\n  title: "A"\n')
        self.assert_problem("cannot be read")

    def test_missing_image(self) -> None:
        self.write("works_2d.yml", '- file: "nope.jpg"\n')
        self.assert_problem('there is no "nope.jpg" in art/2d')

    def test_unknown_field(self) -> None:
        self.picture("2d/a.jpg")
        self.write("works_2d.yml", '- file: "a.jpg"\n  colour: "red"\n')
        self.assert_problem('unknown field "colour"')

    def test_unquoted_hash(self) -> None:
        self.picture("2d/a.jpg")
        self.write("works_2d.yml", '- file: "a.jpg"\n  title: Untitled #4\n')
        self.assert_problem("everything after # is ignored")

    def test_damaged_and_unusable_files(self) -> None:
        (self.root / "art/2d/bad.jpg").write_bytes(b"not a picture")
        (self.root / "art/2d/notes.txt").write_text("hi")
        self.picture("3d/_hidden.jpg")
        self.assert_problem("art/2d/bad.jpg: the picture is damaged")
        self.assert_problem("art/2d/notes.txt: this is not a picture")
        self.assert_problem("names cannot start with")

    def test_artist_home_image_and_links(self) -> None:
        self.write(
            "artist.yml",
            'name: "A"\nhome_image: "art/2d/x.jpg"\nlinks:\n  - name: "I"\n    link: "example.com"\n',
        )
        self.assert_problem('no picture at "art/2d/x.jpg"')
        self.assert_problem("has to start with https://")

    def test_built_pages(self) -> None:
        (self.root / "index.html").write_text('<h1>A</h1><a href="/gone/">x</a><img src="/b.jpg">')
        problems: list[str] = []
        check_built(self.root, problems)
        text = "\n".join(problems)
        self.assertIn("broken link to /gone/", text)
        self.assertIn("no alt text", text)


class ImageTests(SiteCase):
    def test_copies_are_resized_turned_and_stripped(self) -> None:
        exif = Image.Exif()
        exif[ORIENTATION] = 6
        exif[GPS_IFD] = {1: "N", 2: (43.0, 36.0, 0.0)}
        path = self.root / "art/2d/phone.jpg"
        Image.new("RGB", (3000, 2000)).save(path, exif=exif)
        with Image.open(path) as original:
            self.assertTrue(original.getexif().get_ifd(GPS_IFD))
        entry = prepare_all(self.root)["/art/2d/phone.jpg"]
        self.assertGreater(entry["height"], entry["width"])
        for url, longest in ((entry["thumb"], 800), (entry["large"], 2000)):
            with Image.open(self.root / url.lstrip("/")) as copy:
                self.assertEqual(max(copy.size), longest)
                self.assertEqual(len(copy.getexif()), 0)
                self.assertNotIn("xmp", copy.info)

    def test_small_images_are_not_enlarged(self) -> None:
        self.picture("2d/small.png")
        entry = prepare_all(self.root)["/art/2d/small.png"]
        self.assertEqual((entry["width"], entry["height"]), (60, 40))

    def test_transparency_and_other_formats(self) -> None:
        self.picture("2d/clear.png", "RGBA")
        self.picture("2d/print.jpg", "CMYK")
        self.picture("2d/anim.gif", "P")
        self.picture("3d/bird/phone.heic")
        entries = prepare_all(self.root)
        self.assertEqual(len(entries), 4)
        with Image.open(self.root / entries["/art/2d/clear.png"]["thumb"].lstrip("/")) as copy:
            self.assertEqual(copy.mode, "RGBA")


if __name__ == "__main__":
    unittest.main()
