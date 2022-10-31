#!/usr/bin/env python3
# coding: utf-8

import licant
from licant.cxx_modules import application, shared_library, objects
import sys

sys.path.insert(0, "../..")


aret = application(
    "app",
    sources=[
        "main.cpp",
        "ttt.cpp"
    ],
    optimize="-O2")

deps = licant.default_core().depends_as_set("app", incroot=True)
deps = [licant.default_core().get(x) for x in deps]

for d in deps:
    print(d.tgt, d.has_updated_depends(), d.deps)

licant.ex("app")
