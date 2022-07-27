#!/usr/bin/env python3
# coding: utf-8

import sys

sys.path.insert(0, "../..")

import licant.make as lmake
import licant

a = lmake.source("a.txt")
lmake.copy(tgt="build/b.txt", src=a)
lmake.copy(tgt="build/c.txt", src="build/b.txt")

licant.ex("build/c.txt")
