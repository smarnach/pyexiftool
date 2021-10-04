# -*- coding: utf-8 -*-

import shutil
import tempfile
import unittest
from pathlib import Path

from packaging import version

import exiftool

SCRIPT_PATH = Path(__file__).resolve().parent
PERSISTENT_TMP_DIR = False  # if set to true, will not delete temp dir on exit (useful for debugging output)


class TestTagCopying(unittest.TestCase):
    """
    We duplicate an image with metadata, erase all metadata in the copy, and then copy the tags.
    """

    def setUp(self):
        # Prepare exiftool
        self.exiftool = exiftool.ExifToolAlpha(encoding="UTF-8")
        self.exiftool.run()

        # Prepare temporary directory for copy.
        kwargs = {"prefix": "exiftool-tmp-", "dir": SCRIPT_PATH}
        # mkdtemp requires cleanup or else it remains on the system
        if PERSISTENT_TMP_DIR:
            self.temp_obj = None
            self.tmp_dir = Path(tempfile.mkdtemp(**kwargs))
        else:
            self.temp_obj = tempfile.TemporaryDirectory(**kwargs)
            self.tmp_dir = Path(self.temp_obj.name)

        # Find example image.
        self.tag_source = SCRIPT_PATH / "rose.jpg"

        # Prepare path of copy.
        self.tag_target = self.tmp_dir / "rose-tagcopy.jpg"

        # Copy image.
        shutil.copyfile(self.tag_source, self.tag_target)

        # Clear tags in copy.
        params = ["-overwrite_original", "-all=", str(self.tag_target)]
        self.exiftool.execute(*params)

    def tearDown(self):
        self.exiftool.terminate()  # Apparently, Windows needs this.

    def test_tag_copying(self):
        tag = "XMP:Subject"
        expected_value = "Röschen"

        # Ensure source image has correct tag.
        original_value = self.exiftool.get_tag(self.tag_source, tag)
        self.assertEqual(original_value, expected_value)

        # Ensure target image does not already have that tag.
        value_before_copying = self.exiftool.get_tag(self.tag_target, tag)
        self.assertNotEqual(value_before_copying, expected_value)

        # Copy tags.
        self.exiftool.copy_tags(self.tag_source, self.tag_target)

        value_after_copying = self.exiftool.get_tag(self.tag_target, tag)
        self.assertEqual(value_after_copying, expected_value)


class TestExifToolAlpha(unittest.TestCase):
    def setUp(self):
        self.et = exiftool.ExifToolAlpha(
            common_args=["-G", "-n", "-overwrite_original"], encoding="UTF-8"
        )

        # Prepare temporary directory for copy.
        kwargs = {"prefix": "exiftool-tmp-", "dir": SCRIPT_PATH}
        if PERSISTENT_TMP_DIR:
            self.temp_obj = None
            self.tmp_dir = Path(tempfile.mkdtemp(**kwargs))
        else:
            self.temp_obj = tempfile.TemporaryDirectory(**kwargs)
            self.tmp_dir = Path(self.temp_obj.name)

    def tearDown(self):
        if hasattr(self, "et"):
            if self.et.running:
                self.et.terminate()
        if hasattr(self, "process"):
            if self.process.poll() is None:
                self.process.terminate()

    def test_get_metadata(self):
        expected_data = [
            {
                "SourceFile": Path("rose.jpg"),
                "File:FileType": "JPEG",
                "File:ImageWidth": 70,
                "File:ImageHeight": 46,
                "XMP:Subject": "Röschen",
                "Composite:ImageSize": "70 46",
            },
            {
                "SourceFile": Path("skyblue.png"),
                "File:FileType": "PNG",
                "PNG:ImageWidth": 64,
                "PNG:ImageHeight": 64,
                "Composite:ImageSize": "64 64",
            },
        ]
        source_files = []

        for d in expected_data:
            path = SCRIPT_PATH / d["SourceFile"]
            d["SourceFile"] = path
            self.assertTrue(path.exists())
            source_files.append(path)

        with self.et:
            actual_data = self.et.get_metadata(source_files)
            tags0 = self.et.get_tags(source_files[0], ["XMP:Subject"])[0]
            tag0 = self.et.get_tag(source_files[0], "XMP:Subject")

        required_version = version.parse("8.40")
        for expected, actual in zip(expected_data, actual_data):
            actual_version = version.parse(str(actual["ExifTool:ExifToolVersion"]))
            self.assertGreaterEqual(actual_version, required_version)
            actual["SourceFile"] = Path(actual["SourceFile"]).resolve()
            for k, v in expected.items():
                self.assertEqual(actual[k], v)

        tags0["SourceFile"] = Path(tags0["SourceFile"]).resolve()
        self.assertEqual(
            tags0, dict((k, expected_data[0][k]) for k in ["SourceFile", "XMP:Subject"])
        )
        self.assertEqual(tag0, "Röschen")

    def test_set_metadata(self):
        mod_prefix = "newcap_"
        expected_data = [
            {
                "SourceFile": Path("rose.jpg"),
                "Caption-Abstract": "Ein Röschen ganz allein",
            },
            {"SourceFile": Path("skyblue.png"), "Caption-Abstract": "Blauer Himmel"},
        ]
        source_files = []

        for d in expected_data:
            d["SourceFile"] = f = SCRIPT_PATH / d["SourceFile"]
            self.assertTrue(f.exists())

            f_mod = self.tmp_dir / (mod_prefix + f.name)
            f_mod_str = str(f_mod)

            self.assertFalse(
                f_mod.exists(),
                f"{f_mod} should not exist before the test. Please delete.",
            )
            shutil.copyfile(f, f_mod)
            source_files.append(f_mod)
            with self.et:
                self.et.set_tags(f_mod_str, {"Caption-Abstract": d["Caption-Abstract"]})
                tag0 = self.et.get_tag(f_mod_str, "IPTC:Caption-Abstract")
            f_mod.unlink()
            self.assertEqual(tag0, d["Caption-Abstract"])

    def test_set_keywords(self):
        kw_to_add = ["added"]
        mod_prefix = "newkw_"
        expected_data = [
            {"SourceFile": Path("rose.jpg"), "Keywords": ["nature", "red plant"]}
        ]
        source_files = []

        for d in expected_data:
            d["SourceFile"] = f = SCRIPT_PATH / d["SourceFile"]
            self.assertTrue(f.exists())
            f_mod = self.tmp_dir / (mod_prefix + f.name)
            f_mod_str = str(f_mod)
            self.assertFalse(
                f_mod.exists(),
                "%s should not exist before the test. Please delete." % f_mod,
            )

            shutil.copyfile(f, f_mod)
            source_files.append(f_mod)
            with self.et:
                self.et.set_keywords(
                    f_mod_str, exiftool.experimental.KW_REPLACE, d["Keywords"]
                )
                kwtag0 = self.et.get_tag(f_mod_str, "IPTC:Keywords")
                kwrest = d["Keywords"][1:]
                self.et.set_keywords(f_mod_str, exiftool.experimental.KW_REMOVE, kwrest)
                kwtag1 = self.et.get_tag(f_mod_str, "IPTC:Keywords")
                self.et.set_keywords(f_mod_str, exiftool.experimental.KW_ADD, kw_to_add)
                kwtag2 = self.et.get_tag(f_mod_str, "IPTC:Keywords")
            f_mod.unlink()
            self.assertEqual(kwtag0, d["Keywords"])
            self.assertEqual(kwtag1, d["Keywords"][0])
            self.assertEqual(kwtag2, [d["Keywords"][0]] + kw_to_add)


if __name__ == "__main__":
    unittest.main()
