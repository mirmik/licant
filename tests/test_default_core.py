import unittest
import licant
import shutil
import os
import random
import time

from licant.make import copy


class CopyTest(unittest.TestCase):
    def test_core_object(self):
        os.makedirs("/tmp/licant", exist_ok=True)
        # random file name
        tmpname = str(random.randint(0, 1000000))

        # create temporary file
        with open(f"/tmp/licant/test{tmpname}.txt", "w") as f:
            f.write("test")

        copy_target = copy(src=f"/tmp/licant/test{tmpname}.txt",
                           tgt=f"/tmp/licant/test2{tmpname}.txt")

        licant.ex(f"/tmp/licant/test2{tmpname}.txt")

    def test_module_build(self):
        os.makedirs("/tmp/licant", exist_ok=True)
        # random file name
        tmpname = str(random.randint(0, 1000000))

        # create temporary file
        with open(f"/tmp/licant/a{tmpname}.cpp", "w") as f:
            f.write("int main() { return 0; }")

        licant.cxx_application(f"/tmp/licant/a{tmpname}.target",
                               builddir="/tmp/licant/build",
                               sources=[f"/tmp/licant/a{tmpname}.cpp"],
                               )
        licant.ex(f"/tmp/licant/a{tmpname}.target")

        # check if file exists
        self.assertTrue(os.path.exists(f"/tmp/licant/a{tmpname}.target"))
