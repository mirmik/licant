#!/usr/bin/env python3

import sys

sys.path.insert(0, "../..")

import licant
from licant.cxx_modules import application
from licant.libs import include

include("gxx")

application(
    "main",
    target="target",
    sources=["main.cpp"],
    include_modules=[("gxx", "posix"), ("gxx.dprint", "stdout")],
)

licant.ex(default="main")
