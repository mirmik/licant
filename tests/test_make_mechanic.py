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
                           CircularDependencyError,
                           ConnectivityError)


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

    def test_ciclyc_task_2(self):
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

    def test_task_exception_does_not_deadlock(self):
        calls = []

        def a_func():
            calls.append("a")

        def b_func():
            calls.append("b")
            raise RuntimeError("fail")

        def c_func():
            calls.append("c")

        targets = [
            DependableTarget("a", deps={"b", "c"}, what_to_do=a_func),
            DependableTarget("b", deps=set(), what_to_do=b_func),
            DependableTarget("c", deps=set(), what_to_do=c_func),
        ]

        solver = InverseRecursiveSolver(targets, count_of_threads=2)

        result_holder = {"res": None, "exc": None}

        def run_solver():
            try:
                result_holder["res"] = solver.exec()
            except Exception as e:
                result_holder["exc"] = e

        t = threading.Thread(target=run_solver, daemon=True)
        t.start()
        t.join(2.0)  # ждём максимум 2 секунды

        # если поток всё ещё живой — считаем, что дедлок
        self.assertFalse(t.is_alive(), "solver.exec() deadlocked (did not finish in 2 seconds)")

        # если поток упал исключением — тоже важно увидеть
        if result_holder["exc"] is not None:
            raise result_holder["exc"]

        # дальше уже логика поведения
        self.assertIsNotNone(result_holder["res"])
        self.assertFalse(result_holder["res"])  # при ошибке в задаче exec() должен вернуть False

        self.assertIn("b", calls)
        self.assertIn("c", calls)
        self.assertNotIn("a", calls)

    def test_connectivity_error_for_unreachable_cycle(self):
        """Есть нормальный кусок графа и отдельно висящий цикл — должны получить ConnectivityError."""
        def a_func():
            pass
        
        targets = [
            # Связный нормальный участок: b -> a
            DependableTarget("a", deps={"b"}, what_to_do=a_func),
            DependableTarget("b", deps=set(), what_to_do=a_func),

            # Отдельный компонент: цикл c <-> d, до него нельзя дойти от корней
            DependableTarget("c", deps={"d"}, what_to_do=a_func),
            DependableTarget("d", deps={"c"}, what_to_do=a_func),
        ]

        with self.assertRaises(ConnectivityError) as ctx:
            # исключение вылетит уже в __init__
            solver = InverseRecursiveSolver(targets, count_of_threads=1)
            solver.exec()

        # заодно проверим, что в lst именно "висячий" кусок
        names = {t.name() for t in ctx.exception.lst}
        self.assertEqual(names, {"c", "d"})

    def test_target_type_must_be_dependable_target(self):
        """Если в список целей засунули что-то не DependableTarget — должен быть TypeError."""
        def a_func():
            pass

        targets = [
            DependableTarget("a", deps=set(), what_to_do=a_func),
            "not a target at all",
        ]

        with self.assertRaises(TypeError):
            InverseRecursiveSolver(targets, count_of_threads=1)

    def test_dep_type_must_be_str(self):
        """Если зависимость не строка — тоже должен быть TypeError."""
        def a_func():
            pass

        # dep — число, а не строка
        targets = [
            DependableTarget("a", deps={1}, what_to_do=a_func),
        ]

        with self.assertRaises(TypeError):
            InverseRecursiveSolver(targets, count_of_threads=1)
