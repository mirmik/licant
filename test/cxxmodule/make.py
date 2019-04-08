#!/usr/bin/env python3
# coding: utf-8

import sys

sys.path.insert(0, "../..")

from licant.cxx_modules import application, shared_library, objects
import licant

aret = application("app", sources=["main.cpp", "ttt.cpp"])

dret = shared_library("lib", sources=["main.cpp", "ttt.cpp"])

oret = objects("obj", sources=["main.cpp", "ttt.cpp"])

print(aret)
print(dret)
print(oret)

licant.ex()

# print("stree:")
# print(licant.subtree("target"))
# print()
