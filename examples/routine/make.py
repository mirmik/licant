#!/usr/bin/env python3

import licant
import sys

sys.path.insert(0, "../..")

core = licant.Core()


@core.routine(deps=[])
def routine1():
    print("1")


@core.routine(deps=[])
def routine2():
    print("2")


@core.routine(deps=["routine2"])
def routine3():
    print("3")


@core.routine(deps=[])
def routine4(arg0, arg1):
    print(arg0, arg1)


core.do("routine4", args=["Hello", "World"])
licant.ex("routine3", core=core)
