#!/usr/bin/env python3
#coding: utf-8

import sys
sys.path.insert(0, "../..")

from licant.cxx_modules import application
import licant

application("target",
	sources = ["main.cpp", "ttt.cpp"]
)

licant.ex("target")

print("stree:")
print(licant.subtree("target"))
print()