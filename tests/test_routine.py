import unittest
import licant
import shutil
import os


class RoutineTest(unittest.TestCase):
    def test_routine(self):
        x = {}
        core = licant.Core()

        def foo(x):
            x["a"] = 1
        core.target("some_target", action=foo(x))
        core.do("some_target", "action")
        self.assertEqual(x["a"], 1)
