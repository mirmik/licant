#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

import licant.make as lmake
import licant

lmake.source("a.txt")
lmake.copy(tgt = "build/b.txt", src = "a.txt")
lmake.copy(tgt = "build/c.txt", src = "build/b.txt")

print("licant targets list:" + str(licant.core.core.targets))

licant.ex(default = "build/c.txt")