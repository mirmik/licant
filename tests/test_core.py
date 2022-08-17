import unittest
import licant
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

    # def test_target_routine(self):
    #     core = licant.Core()

    #     @core.routine
    #     def clean(target):
    #         licant.system("rm -rf /tmp/licant/test/")

    #     @core.routine
    #     def make(target):
    #         licant.system("mkdir -p /tmp/licant/test/")

    #     self.assertEqual(len(core.targets), 2)
    #     core.do("clean")
    #     core.do("make")
    #     self.assertTrue(os.path.exists("/tmp/licant/test/"))
    #     core.do("clean")
    #     self.assertFalse(os.path.exists("/tmp/licant/test/"))

    # def test_target_depens(self):
    #     core = licant.Core()
    #     x = {"a": 0}
    #     core.updtarget("nonupdated", need_if=lambda s: False)
    #     core.updtarget("target",
    #                    need_if=lambda s: s.has_updated_depends(),
    #                    action=lambda s: setattr(x, "a", 1),
    #                    deps=["nonupdated"]
    #                    )

    #     core.do("target", action="action_if_need")
    #     self.assertEqual(x["a"], 0)
