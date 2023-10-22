# -*- coding: utf-8 -*-
"""
Test :: ExifToolAlpha - misc tests
"""

# standard
import unittest
from pathlib import Path
import shutil

# pip
#from packaging import version

# test helpers
from tests.common_util import et_get_temp_dir, TEST_IMAGE_DIR

# custom
import exiftool




class TestAlphaTagCopying(unittest.TestCase):
    """
    We duplicate an image with metadata, erase all metadata in the copy, and then copy the tags.
    """

    def setUp(self):
        # Prepare exiftool
        self.exiftool = exiftool.ExifToolAlpha(encoding="UTF-8")
        self.exiftool.run()

        # Find example image.
        self.tag_source = TEST_IMAGE_DIR / "rose.jpg"

        # Prepare path of copy.
        (self.temp_obj, self.temp_dir) = et_get_temp_dir(suffix="ttc")
        self.tag_target = self.temp_dir / "rose-tagcopy.jpg"

        # Copy image.
        shutil.copyfile(self.tag_source, self.tag_target)

        # Clear tags in copy.
        params = ["-overwrite_original", "-all=", str(self.tag_target)]
        self.exiftool.execute(*params)

    def tearDown(self):
        self.exiftool.terminate()  # Apparently, Windows needs this.  CPython bug

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


class TestAlphaSetKeywords(unittest.TestCase):
    def setUp(self):
        self.et = exiftool.ExifToolAlpha(
            common_args=["-G", "-n", "-overwrite_original"],
            encoding="UTF-8"
        )


    def tearDown(self):
        self.et.terminate()


    def test_set_keywords(self):
        (temp_obj, temp_dir) = et_get_temp_dir(suffix="setkw")

        kw_to_add = ["added"]
        mod_prefix = "newkw_"
        expected_data = [
            {"SourceFile": Path("rose.jpg"), "Keywords": ["nature", "red plant"]}
        ]
        source_files = []

        for d in expected_data:
            d["SourceFile"] = f = TEST_IMAGE_DIR / d["SourceFile"]
            self.assertTrue(f.exists())
            f_mod = temp_dir / (mod_prefix + f.name)
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
            # f_mod.unlink()  # don't delete file, tempdir will take care of it
            self.assertEqual(kwtag0, d["Keywords"])
            self.assertEqual(kwtag1, d["Keywords"][0])
            self.assertEqual(kwtag2, [d["Keywords"][0]] + kw_to_add)




if __name__ == "__main__":
    unittest.main()
