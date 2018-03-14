#!/usr/bin/env python

import sys
sys.path.insert(0, "../..")

import licant.make as lmake
import licant.cxx_make as lcxx
import licant

lmake.source("a.cpp")
lcxx.object(tgt = "build/a.o", src = "a.cpp")
lcxx.executable(tgt = "target", srcs = ["build/a.o"])

licant.ex(default = "target")