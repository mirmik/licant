import unittest
import licant
import shutil
import os


class FileTest(unittest.TestCase):
    def test_ftarget(self):
        core = licant.MakeCore()
        shutil.rmtree("/tmp/licant/test/", ignore_errors=True)
        os.makedirs("/tmp/licant/test/", exist_ok=True)
        core.ftarget("/tmp/licant/test/1.txt",
                     exec="echo lalala | cat > {tgt}",
                     deps=[])

        core.ftarget("/tmp/licant/test/2.txt",
                     exec="cp {deps[0]} {tgt}",
                     deps=['/tmp/licant/test/1.txt'])

        core.do("/tmp/licant/test/2.txt",
                action="recurse_update")

        self.assertTrue(os.path.exists("/tmp/licant/test/1.txt"))
        self.assertTrue(os.path.exists("/tmp/licant/test/2.txt"))

        with open("/tmp/licant/test/1.txt", "r") as f:
            self.assertEqual(f.read(), "lalala\n")

        with open("/tmp/licant/test/2.txt", "r") as f:
            self.assertEqual(f.read(), "lalala\n")
