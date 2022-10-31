#!/usr/bin/env python3
# coding: utf-8

import licant
from licant import MakeCore
import sys
import os
sys.path.insert(0, "../..")

core = MakeCore()

a = core.source("a.txt")
core.copy(dst="build/b.txt", src=a)
core.copy(dst="build/c.txt", src="build/b.txt")
core.copy(dst="build/d.txt", src="build/b.txt")
core.copy(dst="build/f.txt", src="build/b.txt")

target = core.updtarget("set", deps=["build/d.txt", "build/c.txt"])
target2 = core.updtarget("set2", deps=["set", "build/f.txt"])


@core.routine
def clean():
    print("rm -rf build")
    os.system("rm -rf build")


licant.ex("set2", core=core)
