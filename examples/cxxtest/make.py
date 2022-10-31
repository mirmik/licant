#!/usr/bin/env python3

import licant
import licant.cxx_make as lcxx
import licant.make as lmake
import sys

sys.path.insert(0, "../..")


a = lmake.source("a.cpp")
b = lcxx.object(tgt="build/a.o", src="a.cpp")
c = lcxx.executable(tgt="target", srcs=["build/a.o"])

licant.ex("target")
