#!/usr/bin/env python3
# coding: utf-8

import licant
from licant import MakeCore
import sys
sys.path.insert(0, "../..")

core = MakeCore()

a = core.source("a.txt")
core.copy(dst="build/b.txt", src=a)
core.copy(dst="build/c.txt", src="build/b.txt")

licant.ex("build/c.txt", core=core)
