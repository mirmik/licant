import os
import unittest
import licant
import threading
import licant.util
import shutil
from licant.solver import (DependableTarget,
                           DependableTargetRuntime,
                           InverseRecursiveSolver,
                           UnknowTargetError,
                           NoOneNonDependableTarget,
                           CircularDependencyError)


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
        obj = {"a": False, "b": False, "c": False, "d": False, "e": False}
        l = threading.Lock()

        def a_func():
            with l:
                if not obj["c"] or not obj["b"]:
                    raise Exception("a_func is called before c_func and b_func")
                obj.update({"a": True})

        def b_func():
            with l:
                if not obj["c"] or not obj["e"]:
                    raise Exception("b_func is called before c_func")
                obj.update({"b": True})

        def c_func():
            with l:
                obj.update({"c": True})

        def d_func():
            with l:
                obj.update({"d": True})

        def e_func():
            with l:
                obj.update({"e": True})

        targets = [
            DependableTarget("a", deps={"b", "c"}, what_to_do=lambda: a_func()),
            DependableTarget("b", deps={"c", "e"}, what_to_do=lambda: b_func()),
            DependableTarget("c", deps=set(), what_to_do=lambda: c_func()),
            DependableTarget("d", deps=set(), what_to_do=lambda: d_func()),
            DependableTarget("e", deps=set(), what_to_do=lambda: e_func()),
        ]
        solver = InverseRecursiveSolver(targets, count_of_threads=3)
        self.assertEqual(solver.names_to_deptargets["c"].inverse_deps.__class__, set)
        solver.exec()
        self.assertEqual(obj, {"a": True, "b": True, "c": True, "d": True, "e": True})

    def test_uncorrect_task(self):
        def a_func():
            pass

        targets = [
            DependableTarget("a", deps={"b", "c"}, what_to_do=lambda: a_func()),
            DependableTarget("b", deps={"c", "z"}, what_to_do=lambda: a_func()),
            DependableTarget("c", deps=set(), what_to_do=lambda: a_func()),
            DependableTarget("d", deps=set(), what_to_do=lambda: a_func()),
            DependableTarget("e", deps=set(), what_to_do=lambda: a_func()),
        ]
        with self.assertRaises(UnknowTargetError) as context:
            solver = InverseRecursiveSolver(targets, count_of_threads=3)
            solver.exec()

    def test_ciclyc_task(self):
        def a_func():
            pass

        targets = [
            DependableTarget("a", deps={"b"}, what_to_do=lambda: a_func()),
            DependableTarget("b", deps={"a"}, what_to_do=lambda: a_func()),
        ]
        with self.assertRaises(NoOneNonDependableTarget) as context:
            solver = InverseRecursiveSolver(targets, count_of_threads=1)
            solver.exec()

    def test_ciclyc_task(self):
        def a_func():
            pass

        targets = [
            DependableTarget("a", deps={"b"}, what_to_do=lambda: a_func()),
            DependableTarget("b", deps={"a", "c"}, what_to_do=lambda: a_func()),
            DependableTarget("c", deps=set(), what_to_do=lambda: a_func()),
        ]
        with self.assertRaises(CircularDependencyError) as context:
            solver = InverseRecursiveSolver(targets, count_of_threads=1)
            solver.exec()
