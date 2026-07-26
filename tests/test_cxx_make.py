import os
import unittest
from unittest.mock import patch

from licant.cxx_make import standart_toolchain


class ToolchainTest(unittest.TestCase):
    def test_standard_toolchain_uses_environment(self):
        environment = {
            "CC": "custom-cc",
            "CXX": "custom-cxx",
            "LD": "custom-ld",
            "AR": "custom-ar",
            "OBJDUMP": "custom-objdump",
            "OBJCOPY": "custom-objcopy",
        }

        with patch.dict(os.environ, environment):
            selected = standart_toolchain()

        self.assertEqual(selected.cc, environment["CC"])
        self.assertEqual(selected.cxx, environment["CXX"])
        self.assertEqual(selected.ld, environment["LD"])
        self.assertEqual(selected.ar, environment["AR"])
        self.assertEqual(selected.objdump, environment["OBJDUMP"])
        self.assertEqual(selected.objcopy, environment["OBJCOPY"])
