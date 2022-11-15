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

        core = licant.MakeCore()
        copy_target = core.copy(src=f"/tmp/licant/test{tmpname}.txt",
                                dst=f"/tmp/licant/test2{tmpname}.txt")

        self.assertEqual(len(copy_target.get_deplist()), 1)
        source_target = core.get(copy_target.get_deplist()[0])

        self.assertEqual(1, 1)
        core.do(f"/tmp/licant/test2{tmpname}.txt", action="update_if_need")

        # check if file exists
        self.assertTrue(os.path.exists(f"/tmp/licant/test2{tmpname}.txt"))

        # get source file modification time
        source_mtime = source_target.mtime()

        # get modification time
        mtime = os.path.getmtime(f"/tmp/licant/test2{tmpname}.txt")

        # check test file content
        with open(f"/tmp/licant/test{tmpname}.txt", "r") as f:
            self.assertEqual(f.read(), "test")

        source_mtime2 = source_target.mtime()
        self.assertEqual(source_mtime, source_mtime2)
        time.sleep(0.1)
        with open(f"/tmp/licant/test{tmpname}.txt", "w") as f:
            f.write("tes222t")

        # check test file content
        with open(f"/tmp/licant/test{tmpname}.txt", "r") as f:
            self.assertEqual(f.read(), "tes222t")

        source_target.update_info()

        source_mtime2 = source_target.mtime()
        self.assertNotEqual(source_mtime, source_mtime2)

        time.sleep(0.1)

        core.do(f"/tmp/licant/test2{tmpname}.txt", action="update_if_need")
        self.assertTrue(os.path.exists(f"/tmp/licant/test2{tmpname}.txt"))

        # get modification time
        mtime2 = os.path.getmtime(f"/tmp/licant/test2{tmpname}.txt")

        # check if modification time changed
        self.assertNotEqual(mtime, mtime2)

    def test_double_copy(self):
        os.makedirs("/tmp/licant", exist_ok=True)
        tmpname = str(random.randint(0, 1000000))

        with open(f"/tmp/licant/test{tmpname}.txt", "w") as f:
            f.write("test")

        core = licant.MakeCore()
        copy_target = core.copy(src=f"/tmp/licant/test{tmpname}.txt",
                                dst=f"/tmp/licant/test2{tmpname}.txt")
        source_target = core.get(copy_target.get_deplist()[0])

        core.do(f"/tmp/licant/test2{tmpname}.txt", action="update_if_need")
        copy_mtime_1 = copy_target.mtime()
        core.do(f"/tmp/licant/test2{tmpname}.txt", action="update_if_need")
        copy_mtime_2 = copy_target.mtime()

        self.assertEqual(copy_mtime_1, copy_mtime_2)
