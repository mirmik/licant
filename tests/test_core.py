import unittest
import licant
import shutil
import os


class MyTest(unittest.TestCase):
    def test_core_object(self):
        x = {}
        core = licant.Core()

        def foo(x):
            x["a"] = 1
        core.target("some_target", action=foo(x))
        core.do("some_target", "action")
        self.assertEqual(x["a"], 1)

    def test_target(self):
        core = licant.Core()
        target = core.target("some_target", action=lambda: 1)

        self.assertEqual(target.name(), "some_target")
        self.assertEqual(target.action(), 1)
        self.assertEqual(target.__class__, licant.Target)

    def test_update(self):
        core = licant.Core()
        x = {"a": 0}
        y = {"a": 0}

        def foo(x):
            x["a"] = 1

        core.updtarget("nonupdated", update=lambda s: foo(x),
                       need_if=lambda s: False)
        core.updtarget("updated", update=lambda s: foo(y),
                       need_if=lambda s: True)

        core.do("nonupdated", action="update_if_need")
        core.do("updated", action="update_if_need")

        self.assertEqual(x["a"], 0)
        self.assertEqual(y["a"], 1)

    def test_target_routine(self):
        core = licant.Core()

        @core.routine
        def clean():
            licant.system("rm -rf /tmp/licant/test/")

        @core.routine
        def make():
            licant.system("mkdir -p /tmp/licant/test/")

        self.assertEqual(len(core.targets), 2)
        core.do("clean")
        core.do("make")
        self.assertTrue(os.path.exists("/tmp/licant/test/"))
        core.do("clean")
        self.assertFalse(os.path.exists("/tmp/licant/test/"))

    def test_target_depens(self):
        core = licant.Core(debug=True)
        x = {"a": 0}
        core.updtarget("nonupdated", need_if=lambda s: False)
        core.updtarget("target",
                       update=lambda s: setattr(x, "a", 1),
                       deps=["nonupdated"]
                       )

        self.assertEqual(core.get("target").get_deplist(),
                         [core.get("nonupdated")])

        subtree = core.subtree("target")
        subtree.generate_rdepends()
        self.assertEqual(core.get("nonupdated").rdepends, ["target"])
        self.assertEqual(core.get("target").rdepends, [])
        self.assertEqual(core.get("nonupdated").rcounter, 0)
        self.assertEqual(core.get("target").rcounter, 0)
        self.assertEqual(subtree.depset, ["nonupdated", "target"])

        subtree = core.subtree("target")
        subtree.reverse_recurse_invoke_single("update_if_need")
        self.assertEqual(core.get("nonupdated").rcounter, 0)
        self.assertEqual(core.get("target").rcounter, 1)

        core.do("target", action="recurse_update", kwargs={"threads": 1})
        self.assertEqual(x["a"], 0)

    def test_makecore_touch(self):
        core = licant.MakeCore(debug=True)
        os.makedirs("/tmp/licant/test/", exist_ok=True)
        shutil.rmtree("/tmp/licant/test/", ignore_errors=True)
        target = core.touch("/tmp/licant/test/a", content="Hello")
        core.touch("/tmp/licant/test/d", content="Hello")
        self.assertEqual(
            core.get("/tmp/licant/test").__class__, licant.DirectoryTarget)
        core.do("/tmp/licant/test/a")
        core.do("/tmp/licant/test/d")
        self.assertTrue(os.path.exists("/tmp/licant/test/a"))
        self.assertTrue(os.path.exists("/tmp/licant/test/d"))

        core.copy(src="/tmp/licant/test/a", dst="/tmp/licant/test/b")
        core.copy(src=target, dst="/tmp/licant/test/c")

        core.do("/tmp/licant/test/b")
        core.do("/tmp/licant/test/c")
        self.assertTrue(os.path.exists("/tmp/licant/test/b"))
        self.assertTrue(os.path.exists("/tmp/licant/test/c"))

    def test_source(self):
        core = licant.MakeCore()
        with open("/tmp/vasdvasdva.txt", "w") as f:
            f.write("Hello")
        core.source("a.txt")
        os.remove("/tmp/vasdvasdva.txt")

    def test_copy(self):
        core = licant.MakeCore(debug=True)
        os.makedirs("/tmp/licant/test/", exist_ok=True)
        with open("/tmp/licant/test/a.txt", "w") as f:
            f.write("Hello")
        a = core.source("/tmp/a.txt")
        core.copy(dst="/tmp/licant/test/build/b.txt",
                  src="/tmp/licant/test/a.txt")
        core.copy(dst="/tmp/licant/test/build/c.txt",
                  src="/tmp/licant/test/build/b.txt")

        print(core.get("/tmp/licant/test/a.txt").deps)
        print(core.get("/tmp/licant/test/build/b.txt").deps)
        print(core.get("/tmp/licant/test/build/c.txt").deps)

        self.assertEqual(
            core.get("/tmp/licant/test/build/b.txt").deps, ["/tmp/licant/test/a.txt", "/tmp/licant/test/build"])
        self.assertEqual(core.get(
            "/tmp/licant/test/build/c.txt").deps, ["/tmp/licant/test/build/b.txt", "/tmp/licant/test/build"])

        core.do("/tmp/licant/test/build/c.txt", "recurse_update")
        shutil.rmtree("/tmp/licant")
