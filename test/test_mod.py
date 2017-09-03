#!/usr/bin/env python3.5
#coding: utf-8

import os
import sys
sys.path.insert(0, "..")

from glink.modules import module, submodule
import glink.cxx_modules

glink.scripter.scriptq.execute("src/test.g.py")

module("lib",
	sources=["src/lib.cpp"]
)

module("libimpl", impl = "std",
	sources=["src/aaa.cpp"]
)

module("incm",
	sources=["src/inc.cpp"]
)

module("main",
	srcdir = "src",
	sources = ["main.cpp", "ttt.cpp"],
	include_paths = ["inc"],

	modules=[
		submodule("lib"),
		submodule("libimpl", "std"),
		submodule("lll")
	],

	include_modules=[
		submodule("incm")
	]
)

target = glink.cxx_modules.make("main",
	type = "objects",
	target="target",
	builddir = "build",
	binutils = glink.cxx_make.host_binutils
)


glink.make.doit(target)