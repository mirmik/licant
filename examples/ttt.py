#!/usr/bin/env python3
import os
import unittest
import licant
import threading
import licant.util
import shutil
from licant.solver import (DependableTarget,
                           DependableTargetRuntime,
                           InverseRecursiveSolver)

obj = {"a": False, "b": False, "c": False, "d": False, "e": False}
l = threading.Lock()


def a_func():
    print("A")
    with l:
        if not obj["c"] or not obj["b"]:
            raise Exception("a_func is called before c_func and b_func")
        obj.update({"a": True})


def b_func():
    print("B")
    with l:
        if not obj["c"] or not obj["e"]:
            raise Exception("b_func is called before c_func")
        obj.update({"b": True})


def c_func():
    print("C")
    with l:
        obj.update({"c": True})


def d_func():
    print("D")
    with l:
        obj.update({"d": True})


def e_func():
    print("E")
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
solver.exec()
