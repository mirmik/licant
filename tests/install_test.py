import unittest
import licant
import shutil
import os
import random
import time


class InstallTest(unittest.TestCase):
    def test_touch(self):
        os.makedirs("/tmp/licant", exist_ok=True)
        os.makedirs("/tmp/licant/include", exist_ok=True)

        tmpname = str(random.randint(0, 1000000))

        # create temporary file
        with open(f"/tmp/licant/test{tmpname}.txt", "w") as f:
            f.write("test")

        core = licant.MakeCore()

        files = [
            core.touch(f"/tmp/licant/include/test1{tmpname}.h", "test1"),
            core.touch(f"/tmp/licant/include/test2{tmpname}.h", "test2"),
        ]
        core.do(files, action="build")

        # check if file exists
        self.assertTrue(os.path.exists(
            f"/tmp/licant/include/test1{tmpname}.h"))
        self.assertTrue(os.path.exists(
            f"/tmp/licant/include/test2{tmpname}.h"))

        # check test file content
        with open(f"/tmp/licant/include/test1{tmpname}.h", "r") as f:
            self.assertEqual(f.read(), "test1")

        with open(f"/tmp/licant/include/test2{tmpname}.h", "r") as f:
            self.assertEqual(f.read(), "test2")
