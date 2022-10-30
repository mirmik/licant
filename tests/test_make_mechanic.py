import os
import unittest
import licant
import licant.util
import shutil
from licant.solver import (DependableTarget,
                           DependableTargetRuntime,
                           InverseRecursiveSolver)


class InvertDependsTest(unittest.TestCase):
    def test_invert_depends_dict(self):
        depends_dict = {
            "a": {"b", "c"},
            "b": {"c"},
            "c": {"d"},
            "d": {}
        }

        inverted_dict_result = {
            "a": set(),
            "b": {"a"},
            "c": {"a", "b"},
            "d": {"c"}
        }

        inverted_depends_dictionary = licant.util.invert_depends_dictionary(depends_dict)
        self.assertEqual(inverted_depends_dictionary, inverted_dict_result)

    def test_invert_depends_dict_with_cycle(self):
        depends_dict = {
            "a": {"b", "c"},
            "b": {"c"},
            "c": {"d"},
            "d": {"a"}
        }

        inverted_dict_result = {
            "a": {"d"},
            "b": {"a"},
            "c": {"a", "b"},
            "d": {"c"}
        }

        inverted_depends_dictionary = licant.util.invert_depends_dictionary(depends_dict)
        self.assertEqual(inverted_depends_dictionary, inverted_dict_result)

    def test_InverseRecursiveSolver(self):
        obj = {"a": False, "b": False, "c": False}

        def a_func():
            if not obj["c"] or not obj["b"]:
                raise Exception("a_func is called before c_func and b_func")
            obj.update({"a": True})

        def b_func():
            if not obj["c"]:
                raise Exception("b_func is called before c_func")
            obj.update({"b": True})

        def c_func():
            obj.update({"c": True})

        def d_func():
            obj.update({"d": True})

        def e_func():
            obj.update({"e": True})

        targets = [
            DependableTarget("a", deps={"b", "c"}, what_to_do=lambda: a_func()),
            DependableTarget("b", deps={"c"}, what_to_do=lambda: b_func()),
            DependableTarget("c", deps=set(), what_to_do=lambda: c_func()),
            DependableTarget("d", deps=set(), what_to_do=lambda: d_func()),
            DependableTarget("e", deps=set(), what_to_do=lambda: e_func()),
        ]
        solver = InverseRecursiveSolver(targets, count_of_threads=2)
        self.assertEqual(solver.names_to_deptargets["a"].inverse_deps_count, 0)
        self.assertEqual(solver.names_to_deptargets["b"].inverse_deps_count, 1)
        self.assertEqual(solver.names_to_deptargets["c"].inverse_deps_count, 2)
        self.assertEqual(solver.names_to_deptargets["c"].inverse_deps.__class__, set)
        solver.exec()
        self.assertEqual(obj, {"a": True, "b": True, "c": True, "d": True, "e": True})
